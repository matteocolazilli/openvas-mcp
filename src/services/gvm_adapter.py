"""Utility helpers to interact with the Greenbone Management Protocol (GMP)."""

from __future__ import annotations

import inspect
import dataclasses
import functools
import logging
import re
import types

import xml.etree.ElementTree as etree
from contextlib import contextmanager
from dataclasses import MISSING
from typing import (
    Any,
    Optional,
    TypeVar, 
    Union,
    Sequence,
    Mapping,
    Generator,
    get_args,
    get_origin,
    get_type_hints
)

from gvm.protocols.gmp.requests.v227 import AliveTest
from gvm.utils import SupportsStr
from gvm.connections._connection import AbstractGvmConnection
from gvm.errors import GvmError
from gvm.protocols.gmp import GMPv227 as Gmp
from gvm.transforms import EtreeCheckCommandTransform
from gvm.protocols.gmp.requests.v227 import EntityID, ReportFormatType, HostsOrdering

from xsdata.formats.dataclass.parsers.config import ParserConfig
from xsdata.formats.dataclass.parsers import XmlParser

import src.models.generated as models

logger = logging.getLogger(__name__)
T = TypeVar("T")


class GvmAdapter:
    """
    Adapter for interacting with the Greenbone Management Protocol (GMP).
    Provides methods for managing targets, tasks, and other entities in GVM.
    """

    def __init__(
        self,
        connection: AbstractGvmConnection,
        username: str,
        password: str,
    ) -> None:
        self._connection = connection
        self._username = username
        self._password = password

        self._xml_parser = XmlParser(
            config=ParserConfig(
                fail_on_unknown_properties=False,
                fail_on_unknown_attributes=False,
                class_factory=self._xsdata_class_factory,
            ),
        )

    @staticmethod
    @functools.lru_cache(maxsize=1024)
    def _resolved_type_hints(clazz: type[Any]) -> dict[str, Any]:
        """
        Return the resolved type hints for a class, including any generic type.        
        
        :param clazz: The class to resolve type hints for.
        :type clazz: type[Any]
        :return: A dictionary mapping field names to their resolved types.
        :rtype: dict[str, Any]
        """
        try:
            return get_type_hints(clazz)
        except Exception:  # noqa: BLE001
            return {}

    @staticmethod
    def _allows_none(field_type: Any) -> bool:
        """
        Check if a field type allows None values.

        :param field_type: The type of the field to check.
        :type field_type: Any
        :return: True if the field type allows None, False otherwise.
        :rtype: bool
        """
        if field_type is Any:
            return True
        origin = get_origin(field_type)
        if origin is Union or origin is types.UnionType:
            return type(None) in get_args(field_type)
        return origin is None and type(None) in get_args(field_type)

    @staticmethod
    def _xsdata_class_factory(clazz: type[T], params: dict[str, Any]) -> T:
        """
        Factory function for xsdata to instantiate dataclasses, 
        with special handling for missing fields and empty strings that should be treated as None.        
        
        :param clazz: The class to instantiate.
        :type clazz: type[T]
        :param params: The parameters to initialize the dataclass with.
        :type params: dict[str, Any]
        :return: An instance of the specified dataclass with the provided parameters.
        :rtype: T
        """
        if not dataclasses.is_dataclass(clazz):
            raise TypeError(
                f"xsdata class factory received a non-dataclass type: {clazz!r}"
            )

        resolved = GvmAdapter._resolved_type_hints(clazz)
        field_types = {f.name: resolved.get(f.name, f.type) for f in dataclasses.fields(clazz)}

        cleaned: dict[str, Any] = {}
        for key, value in params.items():
            if value == "" and GvmAdapter._allows_none(field_types.get(key, Any)):
                cleaned[key] = None
            else:
                cleaned[key] = value

        for f in dataclasses.fields(clazz):
            if not f.init:
                continue
            if f.name in cleaned:
                continue
            required = f.default is MISSING and getattr(f, "default_factory", MISSING) is MISSING
            if required:
                cleaned[f.name] = None

        return clazz(**cleaned)  # type: ignore[misc]

    @contextmanager
    def _session(self, authenticate: bool = True) -> Generator[Gmp, None, None]:
        """Yield an authenticated GMP session."""
        with Gmp(
            connection=self._connection, transform=EtreeCheckCommandTransform()
        ) as gmp:
            if authenticate and self._username and self._password:
                gmp.authenticate(self._username, self._password)
            yield gmp

    def _check_method_args(self, command: Any, args: set[str]) -> bool:
        """Check that the provided arguments belong the method signature."""
        if not callable(command):
            raise GvmError(f"Command {command} is not callable")

        sig = inspect.signature(command)
        for arg in args:
            if arg in sig.parameters.keys():
                return True
        return False
    
    def _add_rows_to_filter_string(self, command: Any, kwargs: dict[str, Any]) -> None:
        """Add 'rows=-1' to the filter_string argument if the command supports it.
        
        Args:            
            command: The GMP command to check for filter_string support.
            kwargs: The keyword arguments to potentially modify by adding 'rows=-1' to the filter_string.
        """

        if self._check_method_args(command, ["filter_string"]):
            filter_string = kwargs.get("filter_string") or ""
            # Respect explicit pagination in the caller-provided filter.
            # This keeps default behaviour (no pagination) while still allowing
            # tools to request `rows=1`, `rows=10`, etc.
            if filter_string and re.search(r"(?:^|\\s)rows\\s*=", filter_string):
                return

            kwargs["filter_string"] = f"{filter_string} rows=-1".strip() if filter_string else "rows=-1"

    def _call(
        self, method_name: str, *, authenticate: bool = True, **kwargs: Any
    ) -> etree.Element:
        """Invoke a GMP method with the given arguments."""
        try:
            with self._session(authenticate=authenticate) as gmp:
                command = getattr(gmp, method_name, None)
                if command is None:
                    raise GvmError(f"Unknown GMP method: {method_name}")
                
                # This is needed to avoid pagination and get all results.
                self._add_rows_to_filter_string(command, kwargs)
                logger.debug("Calling GMP method %s with args: %s", method_name, kwargs)
                result: etree.Element = command(**kwargs)
                return result
        except GvmError:
            logger.exception("GMP call %s failed", method_name)
            raise

    def _xml_text(self, root: etree.Element) -> str:
        return etree.tostring(root, encoding="unicode")

    def _parse(self, root: etree.Element, cls: type[T]) -> T:
        return self._xml_parser.from_string(self._xml_text(root), cls)

    def get_targets(
        self,
        *,
        filter_string: Optional[str] = None,
        filter_id: Optional[EntityID] = None,
        trash: Optional[bool] = None,
        tasks: Optional[bool] = None,
    ) -> models.GetTargetsResponse:
        """Request a list of targets.

        Args:
            filter_string: Filter term to use for the query.
            filter_id: UUID of an existing filter to use for the query.
            trash: Whether to include targets in the trashcan.
            tasks: Whether to include list of tasks that use the target.
        """
        root = self._call(
            "get_targets",
            filter_string=filter_string,
            filter_id=filter_id,
            trash=trash,
            tasks=tasks,
        )
        return self._parse(root, models.GetTargetsResponse)

    def get_target(
        self, target_id: EntityID, *, tasks: Optional[bool] = None
    ) -> models.GetTargetsResponse:
        """Request a single target.

        Args:
            target_id: UUID of the target to request.
            tasks: Whether to include list of tasks that use the target
        """
        root = self._call("get_target", target_id=target_id, tasks=tasks)
        return self._parse(root, models.GetTargetsResponse)

    def get_tasks(
        self,
        *,
        filter_string: Optional[str] = None,
        filter_id: Optional[EntityID] = None,
        trash: Optional[bool] = None,
        details: Optional[bool] = None,
        schedules_only: Optional[bool] = None,
        ignore_pagination: Optional[bool] = None,
    ) -> models.GetTasksResponse:
        """Request a list of tasks

        Args:
            filter_string: Filter term to use for the query
            filter_id: UUID of an existing filter to use for the query
            trash: Whether to get the trashcan tasks instead
            details: Whether to include full task details
            schedules_only: Whether to only include id, name and schedule
                details
            ignore_pagination: Whether to ignore pagination settings (filter
                terms "first" and "rows"). Default is False.
        """
        root = self._call(
            "get_tasks",
            filter_string=filter_string,
            filter_id=filter_id,
            trash=trash,
            details=details,
            schedules_only=schedules_only,
            ignore_pagination=ignore_pagination,
        )
        return self._parse(root, models.GetTasksResponse)

    def get_task(self, task_id: EntityID) -> models.GetTasksResponse:
        """Request a single task

        Args:
            task_id: UUID of an existing task
        """
        root = self._call("get_task", task_id=task_id)
        return self._parse(root, models.GetTasksResponse)

    def get_port_lists(
        self,
        *,
        filter_string: Optional[str] = None,
        filter_id: Optional[EntityID] = None,
        details: Optional[bool] = None,
        targets: Optional[bool] = None,
        trash: Optional[bool] = None,
    ) -> models.GetPortListsResponse:
        """Request a list of port lists

        Args:
            filter_string: Filter term to use for the query
            filter_id: UUID of an existing filter to use for the query
            details: Whether to include full port list details
            targets: Whether to include targets using this port list
            trash: Whether to get port lists in the trashcan instead
        """
        root = self._call(
            "get_port_lists",
            filter_string=filter_string,
            filter_id=filter_id,
            details=details,
            targets=targets,
            trash=trash,
        )
        return self._parse(root, models.GetPortListsResponse)

    def create_target(
        self,
        name: str,
        *,
        asset_hosts_filter: Optional[str] = None,
        hosts: Optional[list[str]] = None,
        comment: Optional[str] = None,
        exclude_hosts: Optional[list[str]] = None,
        ssh_credential_id: Optional[EntityID] = None,
        ssh_credential_port: Optional[Union[int, str]] = None,
        smb_credential_id: Optional[EntityID] = None,
        esxi_credential_id: Optional[EntityID] = None,
        snmp_credential_id: Optional[EntityID] = None,
        alive_test: Optional[Union[str, AliveTest]] = None,
        allow_simultaneous_ips: Optional[bool] = None,
        reverse_lookup_only: Optional[bool] = None,
        reverse_lookup_unify: Optional[bool] = None,
        port_range: Optional[str] = None,
        port_list_id: Optional[EntityID] = None,
        ) -> models.CreateTargetResponse:
        """Create a new target

        Args:
            name: Name of the target
            asset_hosts_filter: Filter to select target host from assets hosts
            hosts: List of hosts addresses to scan
            exclude_hosts: List of hosts addresses to exclude from scan
            comment: Comment for the target
            ssh_credential_id: UUID of a ssh credential to use on target
            ssh_credential_port: The port to use for ssh credential
            smb_credential_id: UUID of a smb credential to use on target
            snmp_credential_id: UUID of a snmp credential to use on target
            esxi_credential_id: UUID of a esxi credential to use on target
            alive_test: Which alive test to use
            allow_simultaneous_ips: Whether to scan multiple IPs of the
                same host simultaneously
            reverse_lookup_only: Whether to scan only hosts that have names
            reverse_lookup_unify: Whether to scan only one IP when multiple IPs
                have the same name.
            port_range: Port range for the target
            port_list_id: UUID of the port list to use on target
        """

        root = self._call(
            "create_target",
            name=name,
            asset_hosts_filter=asset_hosts_filter,
            hosts=hosts,
            comment=comment,
            exclude_hosts=exclude_hosts,
            ssh_credential_id=ssh_credential_id,
            ssh_credential_port=ssh_credential_port,
            smb_credential_id=smb_credential_id,
            esxi_credential_id=esxi_credential_id,
            snmp_credential_id=snmp_credential_id,
            alive_test=alive_test,
            allow_simultaneous_ips=allow_simultaneous_ips,
            reverse_lookup_only=reverse_lookup_only,
            reverse_lookup_unify=reverse_lookup_unify,
            port_range=port_range,
            port_list_id=port_list_id,
        )
        return self._parse(root, models.CreateTargetResponse)

    def create_task(
        self,
        name: str,
        config_id: EntityID,
        target_id: EntityID,
        scanner_id: EntityID,
        *,
        alterable: Optional[bool] = None,
        hosts_ordering: Optional[HostsOrdering] = None,
        schedule_id: Optional[EntityID] = None,
        alert_ids: Optional[Sequence[EntityID]] = None,
        comment: Optional[str] = None,
        schedule_periods: Optional[int] = None,
        observers: Optional[Sequence[str]] = None,
        preferences: Optional[Mapping[str, SupportsStr]] = None,
    ) -> models.CreateTaskResponse:
        """Create a new scan task

        Args:
            name: Name of the new task
            config_id: UUID of config to use by the task
            target_id: UUID of target to be scanned
            scanner_id: UUID of scanner to use for scanning the target
            comment: Comment for the task
            alterable: Whether the task should be alterable
            alert_ids: List of UUIDs for alerts to be applied to the task
            hosts_ordering: The order hosts are scanned in
            schedule_id: UUID of a schedule when the task should be run.
            schedule_periods: A limit to the number of times the task will be
                scheduled, or 0 for no limit
            observers: List of names or ids of users which should be allowed to
                observe this task
            preferences: Name/Value pairs of scanner preferences.
        """
        root = self._call(
            "create_task",
            name=name,
            config_id=config_id,
            target_id=target_id,
            scanner_id=scanner_id,
            alterable=alterable,
            hosts_ordering=hosts_ordering,
            schedule_id=schedule_id,
            alert_ids=alert_ids,
            comment=comment,
            schedule_periods=schedule_periods,
            observers=observers,
            preferences=preferences,
        )
        return self._parse(root, models.CreateTaskResponse)

    def start_task(self, task_id: EntityID) -> models.StartTaskResponse:
        """Start an existing task

        Args:
            task_id: UUID of the task to be started
        """
        root = self._call("start_task", task_id=task_id)
        return self._parse(root, models.StartTaskResponse)

    def get_reports(
        self,
        *,
        filter_string: Optional[str] = None,
        filter_id: Optional[EntityID] = None,
        note_details: Optional[bool] = None,
        override_details: Optional[bool] = None,
        ignore_pagination: Optional[bool] = None,
        details: Optional[bool] = None,
    ) -> models.GetReportsResponse:
        """Request a list of reports

        Args:
            filter_string: Filter term to use for the query
            filter_id: UUID of an existing filter to use for the query
            note_details: If notes are included, whether to include note details
            override_details: If overrides are included, whether to include
                override details
            ignore_pagination: Whether to ignore the filter terms "first" and
                "rows".
            details: Whether to exclude results
        """
        root = self._call(
            "get_reports",
            filter_string=filter_string,
            filter_id=filter_id,
            ignore_pagination=ignore_pagination,
            details=details,
            note_details=note_details,
            override_details=override_details,
        )
        return self._parse(root, models.GetReportsResponse)

    def get_report(
        self,
        report_id: EntityID,
        *,
        filter_string: Optional[str] = None,
        filter_id: Optional[str] = None,
        delta_report_id: Optional[EntityID] = None,
        report_format_id: Optional[Union[str, ReportFormatType]] = None,
        ignore_pagination: Optional[bool] = None,
        details: Optional[bool] = True,
    ) -> models.GetReportsResponse:
        """Request a single report

        Args:
            report_id: UUID of an existing report
            filter_string: Filter term to use to filter results in the report
            filter_id: UUID of filter to use to filter results in the report
            delta_report_id: UUID of an existing report to compare report to.
            report_format_id: UUID of report format to use
                              or ReportFormatType (enum)
            ignore_pagination: Whether to ignore the filter terms "first" and
                "rows".
            details: Request additional report information details
                     defaults to True
        """
        root = self._call(
            "get_report",
            report_id=report_id,
            filter_string=filter_string,
            filter_id=filter_id,
            delta_report_id=delta_report_id,
            report_format_id=report_format_id,
            report_config_id=None,
            ignore_pagination=ignore_pagination,
            details=details,
        )
        return self._parse(root, models.GetReportsResponse)

    def get_scanners(
        self,
        *,
        filter_string: Optional[str] = None,
        filter_id: Optional[EntityID] = None,
        trash: Optional[bool] = None,
        details: Optional[bool] = None,
    ) -> models.GetScannersResponse:
        """Request a list of scanners

        Args:
            filter_string: Filter term to use for the query
            filter_id: UUID of an existing filter to use for the query
            trash: Whether to get the trashcan scanners instead
            details: Whether to include extra details like tasks using this
                scanner
        """
        root = self._call(
            "get_scanners",
            filter_string=filter_string,
            filter_id=filter_id,
            details=details,
            trash=trash,
        )
        return self._parse(root, models.GetScannersResponse)

    def get_scan_configs(
        self,
        *,
        filter_string: Optional[str] = None,
        filter_id: Optional[EntityID] = None,
        trash: Optional[bool] = None,
        details: Optional[bool] = None,
        families: Optional[bool] = None,
        preferences: Optional[bool] = None,
        tasks: Optional[bool] = None
    ) -> models.GetConfigsResponse:
        """Request a list of scan configs

        Args:
            filter_string: Filter term to use for the query
            filter_id: UUID of an existing filter to use for the query
            trash: Whether to get the trashcan scan configs instead
            details: Whether to get config families, preferences, nvt selectors
                and tasks.
            families: Whether to include the families if no details are
                requested
            preferences: Whether to include the preferences if no details are
                requested
            tasks: Whether to get tasks using this config
        """
        root = self._call(
            "get_scan_configs",
            filter_string=filter_string,
            filter_id=filter_id,
            trash=trash,
            details=details,
            families=families,
            preferences=preferences,
            tasks=tasks
        )
        return self._parse(root, models.GetConfigsResponse)
