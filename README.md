# indigo build system

## Description

C++20 modules build system written from scratch.
Supports C and C++ translation units. <br>
**Meant** to be used in indie projects for fun. <br>
**Not meant** to revolutionize the world of C/C++ build systems. <br>
You can build this repository by simply `py __init__.py build`.

## Requirements

- Microsoft C++ build tools ;; Launch-VsDevShell.ps1
- Python >=3.10 ;; match statement

## Schema

Source file types:

- .hxx :: header unit
- .ixx :: module interface
- .cxx :: module implementation
- ~~.tbdxx~~ :: internal partition ;; Don't feel like it is of any use right now
- .c :: C translation unit
- .cpp :: C++ translation unit

> Note: <br>
> : Source files `main.c` and `main.cpp` are reserved for `int main(int, char**)` functions. <br>
> : Indigo tries to produce an executable if translation unit with such name is discovered.

## Motivation

> Why not just use CMake?

cmake:

- [x] ugly syntax
- [x] requires to google every other function/option/parameter
- [x] prehistoric decisions and backwards compatibility all the way to the dinosaurs era
- [x] can't rapidly plug something in
- [x] can't build indigo projects
- [ ] ~~stinks~~

indigo:

- [x] static analysis and debugging due to the python backend
- [x] easy to dive in thanks to type annotatins
- [x] simple and extensible
- [x] supports MSVC modules
- [x] could build cmake projects

## Compatibility

- [x] windows msvc
- [ ] windows non-msvc (not planned)
- [ ] non-windows (not planned)

## Todo

### Work in-progress

- [ ] Solution
  - [ ] encapsulate multi-project configurations ;; indigo/solution.py
  - [ ] explicit target project argument to clean/build/rebuild/test commands
- [ ] MSVC Project
  - [ ] implement dynamic libraries
- [ ] Options
  - [ ] explicit project options (flags, includes, libraries and etc)

### Planned

- [ ] tests
  - [ ] input/output schema
  - [ ] output validation
  - [ ] --record option to save tests output as ethalon for future validations
  - [ ] feed input to tests

### Postponed

- [ ] ~~Explore~~ globs for Project.source_files. ;; Personally, I'd rather explicitly specify source files and their build order.
- [ ] ~~Analyze~~ source files imports and includes for incremental builds. ;; Not concerned yet. Thanks to multi-processing rebuild is fast enough.

## License

unlicense: <https://unlicense.org> <br>
author: <vincent@newbject.com>
