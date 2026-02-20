# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Matteo Colazilli
# Portions adapted from python-gvm, Copyright (C) Greenbone AG,
# licensed under GPL-3.0-or-later.

"""
Utility helpers to interact with the Greenbone Management Protocol (GMP).
"""

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
    Iterable,
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
from gvm.connections import UnixSocketConnection, DEFAULT_UNIX_SOCKET_PATH
from gvm.errors import GvmError
from gvm.protocols.gmp import GMPv227 as Gmp
from gvm.transforms import EtreeCheckCommandTransform
from gvm.protocols.gmp.requests.v227 import EntityID, ReportFormatType, HostsOrdering

from xsdata.formats.dataclass.parsers.config import ParserConfig
from xsdata.formats.dataclass.parsers import XmlParser

import src.models.generated as models

logger = logging.getLogger(__name__)
T = TypeVar("T")


class GvmClient:
    """
    Client for interacting with the Greenbone Management Protocol (GMP).

    Provides methods for managing targets, tasks, and other entities in GVM.
    """

    def __init__(
        self,
        username: str,
        password: str,
    ) -> None:
        self._connection = UnixSocketConnection(path=DEFAULT_UNIX_SOCKET_PATH)
        self._transform = EtreeCheckCommandTransform()
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
        Return resolved type hints for a class.

        Args:
            clazz (type[Any]): Class to resolve type hints for.

        Returns:
            dict[str, Any]: Mapping of field names to resolved types.
        """
        try:
            return get_type_hints(clazz)
        except TypeError:
            return {}

    @staticmethod
    def _allows_none(field_type: Any) -> bool:
        """
        Check if a field type allows None values.

        Args:
            field_type (Any): Field type to inspect.

        Returns:
            bool: True if the field type accepts None, otherwise False.
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
        Instantiate dataclasses for xsdata parsing.

        Empty strings are converted to None when the target field supports None,
        and missing required init fields are populated with None.

        Args:
            clazz (type[T]): Dataclass type to instantiate.
            params (dict[str, Any]): Constructor parameters from parsed XML.

        Returns:
            T: Instantiated dataclass object.

        Raises:
            TypeError: If clazz is not a dataclass.
        """
        if not dataclasses.is_dataclass(clazz):
            raise TypeError(
                f"xsdata class factory received a non-dataclass type: {clazz!r}"
            )

        resolved = GvmClient._resolved_type_hints(clazz)
        field_types = {f.name: resolved.get(f.name, f.type) for f in dataclasses.fields(clazz)}

        cleaned: dict[str, Any] = {}
        for key, value in params.items():
            if value == "" and GvmClient._allows_none(field_types.get(key, Any)):
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
        """
        Yield a GMP session.

        Args:
            authenticate (bool): Whether to authenticate with configured credentials.

        Yields:
            Generator[Gmp, None, None]: Active GMP session.
        """
        with Gmp(
            connection=self._connection, transform=self._transform
        ) as gmp:
            if authenticate and self._username and self._password:
                gmp.authenticate(self._username, self._password)
            yield gmp

    def _check_method_args(self, command: Any, args: Iterable[str]) -> bool:
        """
        Check whether at least one argument is supported by a command signature.

        Args:
            command (Any): Callable GMP command.
            args (Iterable[str]): Argument names to validate.

        Returns:
            bool: True if any provided argument exists in the command signature.

        Raises:
            GvmError: If command is not callable.
        """
        if not callable(command):
            raise GvmError(f"Command {command} is not callable")

        sig = inspect.signature(command)
        for arg in args:
            if arg in sig.parameters.keys():
                return True
        return False
    
    def _add_rows_to_filter_string(self, command: Any, kwargs: dict[str, Any]) -> None:
        """
        Add `rows=-1` to `filter_string` when supported and not already specified.

        Args:
            command (Any): GMP command to inspect.
            kwargs (dict[str, Any]): Keyword arguments to mutate in place.
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
        """
        Invoke a GMP method with the given arguments.

        Args:
            method_name (str): GMP method name to invoke.
            authenticate (bool): Whether to authenticate the session first.
            **kwargs (Any): Keyword arguments forwarded to the GMP method.

        Returns:
            etree.Element: XML response returned by GMP.

        Raises:
            GvmError: If the method does not exist or GMP call fails.
        """
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
        """
        Convert an XML element to a Unicode string.

        Args:
            root (etree.Element): XML root element.

        Returns:
            str: Serialized XML.
        """
        return etree.tostring(root, encoding="unicode")

    def _parse(self, root: etree.Element, cls: type[T]) -> T:
        """
        Parse an XML element into a typed model.

        Args:
            root (etree.Element): XML root element to parse.
            cls (type[T]): Target model class.

        Returns:
            T: Parsed model instance.
        """
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
            filter_string (Optional[str]): Filter term for the query.
            filter_id (Optional[EntityID]): Existing filter UUID for the query.
            trash (Optional[bool]): Whether to include targets in the trashcan.
            tasks (Optional[bool]): Whether to include tasks using each target.

        Returns:
            models.GetTargetsResponse: Targets response payload.
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
            target_id (EntityID): Target UUID to request.
            tasks (Optional[bool]): Whether to include tasks using the target.

        Returns:
            models.GetTargetsResponse: Target response payload.
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
        """
        Request a list of tasks.

        Args:
            filter_string (Optional[str]): Filter term for the query.
            filter_id (Optional[EntityID]): Existing filter UUID for the query.
            trash (Optional[bool]): Whether to get trashcan tasks instead.
            details (Optional[bool]): Whether to include full task details.
            schedules_only (Optional[bool]): Whether to include only id, name,
                and schedule details.
            ignore_pagination (Optional[bool]): Whether to ignore `first` and
                `rows` filter terms.

        Returns:
            models.GetTasksResponse: Tasks response payload.
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
        """
        Request a single task.

        Args:
            task_id (EntityID): Existing task UUID.

        Returns:
            models.GetTasksResponse: Task response payload.
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
        """
        Request a list of port lists.

        Args:
            filter_string (Optional[str]): Filter term for the query.
            filter_id (Optional[EntityID]): Existing filter UUID for the query.
            details (Optional[bool]): Whether to include full port-list details.
            targets (Optional[bool]): Whether to include targets using the port list.
            trash (Optional[bool]): Whether to get trashcan port lists instead.

        Returns:
            models.GetPortListsResponse: Port lists response payload.
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
        """
        Create a new target.

        Args:
            name (str): Target name.
            asset_hosts_filter (Optional[str]): Filter selecting target hosts from assets.
            hosts (Optional[list[str]]): Host addresses to scan.
            comment (Optional[str]): Target comment.
            exclude_hosts (Optional[list[str]]): Host addresses to exclude from scan.
            ssh_credential_id (Optional[EntityID]): SSH credential UUID.
            ssh_credential_port (Optional[Union[int, str]]): SSH port.
            smb_credential_id (Optional[EntityID]): SMB credential UUID.
            esxi_credential_id (Optional[EntityID]): ESXi credential UUID.
            snmp_credential_id (Optional[EntityID]): SNMP credential UUID.
            alive_test (Optional[Union[str, AliveTest]]): Alive test mode.
            allow_simultaneous_ips (Optional[bool]): Whether to scan multiple IPs
                of the same host simultaneously.
            reverse_lookup_only (Optional[bool]): Whether to scan only hosts that
                resolve to names.
            reverse_lookup_unify (Optional[bool]): Whether to scan only one IP when
                multiple IPs share the same name.
            port_range (Optional[str]): Explicit port range.
            port_list_id (Optional[EntityID]): Port list UUID to use.

        Returns:
            models.CreateTargetResponse: Target creation response payload.
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
        """
        Create a new scan task.

        Args:
            name (str): Task name.
            config_id (EntityID): Scan config UUID.
            target_id (EntityID): Target UUID.
            scanner_id (EntityID): Scanner UUID.
            alterable (Optional[bool]): Whether the task is alterable.
            hosts_ordering (Optional[HostsOrdering]): Host scan order mode.
            schedule_id (Optional[EntityID]): Schedule UUID for task execution.
            alert_ids (Optional[Sequence[EntityID]]): Alert UUIDs applied to task.
            comment (Optional[str]): Task comment.
            schedule_periods (Optional[int]): Number of schedule repetitions,
                or 0 for no limit.
            observers (Optional[Sequence[str]]): User names or ids allowed to
                observe this task.
            preferences (Optional[Mapping[str, SupportsStr]]): Scanner preference
                name/value pairs.

        Returns:
            models.CreateTaskResponse: Task creation response payload.
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
        """
        Start an existing task.

        Args:
            task_id (EntityID): Task UUID to start.

        Returns:
            models.StartTaskResponse: Task start response payload.
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
        """
        Request a list of reports.

        Args:
            filter_string (Optional[str]): Filter term for the query.
            filter_id (Optional[EntityID]): Existing filter UUID for the query.
            note_details (Optional[bool]): Whether to include note details.
            override_details (Optional[bool]): Whether to include override details.
            ignore_pagination (Optional[bool]): Whether to ignore `first` and
                `rows` filter terms.
            details (Optional[bool]): Whether to include extra report details.

        Returns:
            models.GetReportsResponse: Reports response payload.
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
        """
        Request a single report.

        Args:
            report_id (EntityID): Existing report UUID.
            filter_string (Optional[str]): Filter term for report results.
            filter_id (Optional[str]): Filter UUID for report results.
            delta_report_id (Optional[EntityID]): Report UUID used for comparison.
            report_format_id (Optional[Union[str, ReportFormatType]]): Report
                format UUID or enum.
            ignore_pagination (Optional[bool]): Whether to ignore `first` and
                `rows` filter terms.
            details (Optional[bool]): Whether to request additional report details.

        Returns:
            models.GetReportsResponse: Report response payload.
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
        """
        Request a list of scanners.

        Args:
            filter_string (Optional[str]): Filter term for the query.
            filter_id (Optional[EntityID]): Existing filter UUID for the query.
            trash (Optional[bool]): Whether to get trashcan scanners instead.
            details (Optional[bool]): Whether to include extra details such as
                tasks using each scanner.

        Returns:
            models.GetScannersResponse: Scanners response payload.
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
        """
        Request a list of scan configs.

        Args:
            filter_string (Optional[str]): Filter term for the query.
            filter_id (Optional[EntityID]): Existing filter UUID for the query.
            trash (Optional[bool]): Whether to get trashcan scan configs instead.
            details (Optional[bool]): Whether to include config families,
                preferences, NVT selectors, and tasks.
            families (Optional[bool]): Whether to include families when `details`
                is not requested.
            preferences (Optional[bool]): Whether to include preferences when
                `details` is not requested.
            tasks (Optional[bool]): Whether to include tasks using each config.

        Returns:
            models.GetConfigsResponse: Scan configs response payload.
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

    def stop_task(self, task_id: EntityID) -> models.StopTaskResponse:
        """
        Stop a running task.

        Args:
            task_id (EntityID): Task UUID to stop.

        Returns:
            models.StopTaskResponse: Task stop response payload.
        """
        root = self._call("stop_task", task_id=task_id)
        return self._parse(root, models.StopTaskResponse)