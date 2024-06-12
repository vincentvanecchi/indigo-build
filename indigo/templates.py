exported_dataclass_template = '''{imports}
{property} = {object}'''

hxx_template = '''#pragma once

#include <c_header.h>
#include <cpp_header.hpp>

import {module};

namespace {namespace}::detail {{
    // ...
}} // namespace {namespace}::detail
'''

ixx_template = '''module;
#include <c_header.h>
#include <cxx_header.hpp>
export module {module};

import <header_unit.hxx>;

export namespace {namespace} {{
    
    class T {{
        struct S;
        S* impl_{{nullptr}};
    public:
        T() = default;
        ~T() = default;

        T(const T& o) = delete;
        T& operator=(const T& o) = delete;

        T(T&& o) noexcept;
        T& operator=(T&& o) noexcept;

        explicit T(auto&&... args);

        void __init__(auto&&... args);
        void __del__() noexcept;

        void __enter__();
        void __exit__(auto exception) noexcept;

        operator bool() const noexcept;

        auto operator <=>(const T& o) const noexcept;
    }};

}} // namespace {namespace}
'''

cxx_template = '''module;
#include <c_header.h>
#include <cxx_header.hpp>
module {module};

namespace {namespace} {{

    T::operator bool() const noexcept {{
        return this->impl_ != nullptr;
    }}

}} // namespace {namespace}
'''

cpp_template = '''import {module};

using namespace {namespace};

// ...
'''

main_cpp_template = '''import {module};

int main(int ac, char** av) {{
    (void)ac;
    (void)av;
    {namespace}::T t;
    return 0;
}}
'''

uxx_template = '''import {module};

int main(int ac, char** av) {{
    (void)ac;
    (void)av;
    {namespace}::T t;
    // any testing?
    return 0;
}}
'''