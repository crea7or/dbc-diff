# DBCDiff

**DBCDiff** is a Python-based command-line tool for comparing individual DBC files or entire folders containing DBC files. It generates comparison reports in various formats such as **JSON**, **HTML**, or **Whatever**. The reporting system is extensible, allowing you to add custom templates for new report types.

---

## Features

- Compare single DBC files or directories containing multiple DBC files.
- Identify changes, additions, and deletions between two sets of DBC files.
- Optionally include unchanged DBC files in the report.
- Generate reports in multiple formats (**json**, **html**, etc.).
- Extendable report templates for custom output formats.

---

## Installation

Clone the repository and install the required dependencies:

```bash
pip install -r requirements.txt
```

```bash
python dbcdiff.py [OPTIONS]
```

Option                   | Description
------------------------ | -----------
`-f, --old, --from PATH` | Path to the old DBC file or folder (required).
`-t, --new, --to PATH`   | Path to the new DBC file or folder (required).
`-u, --unchanged`        | Include in the report DBCs that are not changed.
`-r, --reports TEXT`     | Comma-delimited list of report types to generate (e.g. `json,html,md`). **Required**
`-i, --info TEXT`        | Additional information to display in the report (e.g. "Release 1.2 vs 1.3").
`-n, --name TEXT`        | Base name for the output report files (e.g., `diff_report` → `diff_report.json`).
`-o, --output PATH`      | Output folder where the generated reports will be saved.
`--help`                 | Show help message and exit.


Example:
```bash
python dbcdiff.py -f ./old_dbcs -t ./new_dbcs -r html,json -i "Release v1.0 vs v2.0"
```


![image](https://github.com/crea7or/dbc-diff/blob/master/dbcdiff.png)

MIT License Copyright (c) 2022 pavel.sokolov@gmail.com / CEZEO software Ltd.. All rights reserved.

```
      .:+oooooooooooooooooooooooooooooooooooooo: `/ooooooooooo/` :ooooo+/-`
   `+dCEZEOCEZEOCEZEOCEZEOCEZEOCEZEOCEZEOCEZEOEZshCEZEOCEZEOEZ#doCEZEOEZEZNs.
  :CEZEON#ddddddddddddddddddddddddddddddNCEZEO#h.:hdddddddddddh/.yddddCEZEO#N+
 :CEZEO+.        .-----------.`       `+CEZEOd/   .-----------.        `:CEZEO/
 CEZEO/         :CEZEOCEZEOEZNd.    `/dCEZEO+`   sNCEZEOCEZEO#Ny         -CEZEO
 CEZEO/         :#NCEZEOCEZEONd.   :hCEZEOo`     oNCEZEOCEZEO#Ny         -CEZEO
 :CEZEOo.`       `-----------.`  -yNEZ#Ns.       `.-----------.`       `/CEZEO/
  :CEZEONCEZEOd/.ydCEZEOCEZEOdo.sNCEZEOCEZEOCEZEOCEZEOCEZEOCEZEOCEZEOEZNEZEZN+
   `+dCEZEOEZEZdoCEZEOCEZEOEZ#N+CEZEOCEZEOCEZEOCEZEOCEZEOCEZEOCEZEOCEZEOEZ#s.
      .:+ooooo/` :+oooooooooo+. .+ooooooooooooooooooooooooooooooooooooo+/.

 C E Z E O  S O F T W A R E (c) 2025   DBC diff / compare tool / release notes builder
                        MIT License / pavel.sokolov@gmail.com
```