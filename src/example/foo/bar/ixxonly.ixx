module;
#include <c_header.h>
#include <cxx_header.hpp>
export module example.foo.bar.ixxonly;

import <header_unit.hxx>;

export namespace example::foo::bar::ixxonly {
    // ...
} // namespace example::foo::bar::ixxonly
