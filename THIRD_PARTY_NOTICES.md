# Third-Party Notices

This repository includes and depends on third-party open-source software.

This file documents the main direct dependencies declared in `pyproject.toml` and their licenses.
It does **not** replace the original license texts of upstream projects.

## Project License

`GreenboneMCP` is licensed under:

- **GPL-3.0-or-later**

See [`LICENSE.md`](LICENSE.md) for the full text.

## Direct Dependencies and Licenses

| Package | Declared dependency | License (SPDX) | Copyright / Author | Upstream |
|---|---|---|---|---|
| fastmcp | `fastmcp==2.14.5` | Apache-2.0 | Jeremiah Lowin (and contributors) | https://pypi.org/project/fastmcp/ |
| python-gvm | `python-gvm==26.9.1` | GPL-3.0-or-later | Greenbone AG | https://pypi.org/project/python-gvm/ |
| pydantic | `pydantic==2.11.7` | MIT | Samuel Colvin (and contributors) | https://pypi.org/project/pydantic/ |
| pydantic-settings | `pydantic-settings==2.10.1` | MIT | Samuel Colvin (and contributors) | https://pypi.org/project/pydantic-settings/ |
| xsdata (extra: cli) | `xsdata[cli]==26.1` | MIT | Christodoulos Tsoulloftas | https://pypi.org/project/xsdata/ |

## Attribution and Adaptation Notice (python-gvm)

This project includes a wrapper around `python-gvm` APIs.  
Where method signatures and/or descriptive text are adapted from `python-gvm`, those adapted portions remain attributable to the original project and are distributed in compliance with GPL-3.0-or-later terms.

## No Endorsement

Use of third-party names does not imply endorsement by their respective owners.
All trademarks are property of their respective owners.
