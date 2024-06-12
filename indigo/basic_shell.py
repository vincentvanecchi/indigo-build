
import subprocess
from typing import Callable
from dataclasses import dataclass

from indigo.filesystem import PathLike, get_file_name

def _Shell_Exec(
    executable: PathLike,
    args: tuple|str = tuple(), 
    logger: Callable[[str, str, str], None] = None,
    parser: Callable[[str, str, int], tuple[str, str, int]] = None
) -> tuple[str, str, int]:
    assert executable

    if logger:
        logger(get_file_name(executable), None, ' '.join(args))

    r = subprocess.run(executable=executable, args=args, capture_output=True)
    
    stdout = r.stdout.decode().strip()
    stderr = r.stderr.decode().strip()
    returncode = r.returncode

    if parser:
        return parser(stdout, stderr, returncode)
    else:
        return (stdout, stderr, returncode)

@dataclass 
class _Async_Command:
    name: str
    executable: PathLike
    process: subprocess.Popen = None
    logger: Callable[[str, str, tuple|str], None] = None
    parser: Callable[[str, str, int], tuple[str, str, int]] = None

    def _Await(self, input = None, timeout = None) -> tuple[str, str, int]:
        returncode = 0
        stdout = b''
        stderr = b''
        with self.process:
            try:
                stdout, stderr = self.process.communicate(input=input, timeout=timeout)
            except subprocess.TimeoutExpired as exc:
                self.process.kill()
                if subprocess._mswindows:
                    # Windows accumulates the output in a single blocking
                    # read() call run on child threads, with the timeout
                    # being done in a join() on those threads.  communicate()
                    # _after_ kill() is required to collect that and add it
                    # to the exception.
                    exc.stdout, exc.stderr = self.process.communicate()
                else:
                    # POSIX _communicate already populated the output so
                    # far into the TimeoutExpired exception.
                    self.process.wait()
                raise
            except:  # Including KeyboardInterrupt, communicate handled that.
                self.process.kill()
                # We don't call process.wait() as .__exit__ does that for us.
                raise
            returncode = self.process.poll()

        self.logger('await', self.name, '')
        
        stdout = stdout.decode().strip()
        stderr = stderr.decode().strip()

        if self.parser:
            return self.parser(stdout, stderr, returncode)
        else:
            return (stdout, stderr, returncode)

def _Shell_Exec_Async(
    name: str,
    executable: PathLike,
    args: tuple|str = tuple(), 
    logger: Callable[[str, str, str], None] = None,
    parser: Callable[[str, str, int], tuple[str, str, int]] = None
) -> _Async_Command:
    if logger:
        logger('async', name, ' '.join(args))

    return _Async_Command(
        name=name,
        executable=executable,
        process=subprocess.Popen(executable=executable, 
                                args=args, 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE
                                ),
        logger=logger,
        parser=parser
    )
