from indigo import Solution, CompilationError, TestingError, console_text_styles

if __name__ == '__main__':
    solution = Solution._Import()
    try:
        argument_parser = solution.argument_parser()
        # argument_parser.add_argument('--custom')
        args = argument_parser.parse_args()
        console_text_styles.cts_print(
            section='solution', 
            subsection=solution.name, 
            text=f'executing :: command: {console_text_styles.cts_warning(args.command)}; ' \
            + f'target: {console_text_styles.cts_warning(args.target or "all")}'
        )
        solution.on_command(args)
    except CompilationError:
        console_text_styles.cts_print(
            section='solution', 
            subsection=solution.name, 
            text=f'building :: {console_text_styles.cts_fail("FAILED")}'
        )
        exit(1)
    except TestingError:
        console_text_styles.cts_print(
            section='solution', 
            subsection=solution.name, 
            text=f'testing :: {console_text_styles.cts_fail("FAILED")}'
        )
        exit(2)
