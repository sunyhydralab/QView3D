import math
import os
import re
import sys
import pytest
from _pytest.terminal import TerminalWriter, TerminalReporter


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    for arg in config.invocation_params.args:
        if arg.startswith("--port="):
            config.port = arg.split("=")[1]
    config.logger = setup_logger(config.port)
    logger = config.logger
    myTR = TerminalReporter(config)
    myTR.__repr__ = lambda: "My Terminal Reporter"
    myTW = myTR._tw
    myTW.__repr__ = lambda: "My Terminal Writer"
    myTW.logLine: str = ""
    myTW.fullwidth = 113
    myTR._screen_width = myTW.fullwidth
    myTW.hasmarkup = True

    def custom_write(self: TerminalWriter, msg: str, *, flush: bool = False, **markup: bool):
        if msg:
            current_line = msg.rsplit("\n", 1)[-1]
            if "\n" in msg:
                self._current_line = current_line
            else:
                self._current_line += current_line

            msg = self.markup(msg, **markup)
            log = msg.strip()

            try:
                if log:
                    if self.logLine == "":
                        self.logLine = msg
                    else:
                        self.logLine = " ".join([self.logLine, msg])
                    if flush:
                        self.logLine = self.logLine.strip()
                        if "red" in markup and markup["red"] == True:
                            logger.error(self.logLine)
                        elif "yellow" in markup and markup["yellow"] == True:
                            logger.warning(self.logLine)
                        else:
                            logger.info(self.logLine)
                        self.logLine = ""
                self._file.write(msg)
            except UnicodeEncodeError:
                msg = msg.encode("unicode-escape").decode("ascii")
                self._file.write(msg)

            if flush:
                self.flush()

    myTW.write = custom_write.__get__(myTW, TerminalWriter)
    terminal_reporter = config.pluginmanager.get_plugin("terminalreporter")
    if terminal_reporter:
        config.pluginmanager.unregister(terminal_reporter)
        config.pluginmanager.register(myTR, "terminalreporter")
    else:
        config.pluginmanager.register(myTR, "terminalreporter")

    config.terminalReporter = myTR


@pytest.fixture(scope="session", autouse=True)
def fabricator(request, app):
    port = request.session.config.port
    if not port: return None
    from serial.tools.list_ports_common import ListPortInfo
    from serial.tools.list_ports_linux import SysFS
    if isinstance(port, str):
        fabricator = app.fabricator_list.getFabricatorByPort(port)
    elif isinstance(port, ListPortInfo) or isinstance(port, SysFS):
        fabricator = app.fabricator_list.getFabricatorByPort(port.device)
    else:
        fabricator = None
    if fabricator is None:
        pytest.skip("No port specified")
    if os.getenv("LEVEL") == "DEBUG":
        fabricator.device.logger.setLevel(fabricator.device.logger.DEBUG)
    fabricator.device.connect()
    yield fabricator
    fabricator.device.disconnect()

# @pytest.fixture(scope="session", autouse=True)
# def client(request, app):
#     client = Client(logger=True)
#     port = request.session.config.port
#     portNum = int(port.split("COM")[-1])
#     clientPort = portNum + 5000
#     client.connect(f"http://localhost:{clientPort}")
#     app.client = client
#     yield client
#     client.disconnect()

@pytest.fixture(scope="session", autouse=True)
def app():
    from services.app_service import current_app as app
    with app.app_context():
        yield app
        app.fabricator_list.teardown()


from Classes.Loggers.Logger import Logger

intLogger = Logger("Internal Errors", consoleLogger=sys.stdout, fileLogger="internal_errors.log", loggingLevel=Logger.INFO)

# def pytest_internalerror(excrepr, excinfo):
#     # This hook is called when pytest encounters an internal error
#     intLogger.error(f"Internal pytest error:\n{excrepr}")

def pytest_addoption(parser):
    parser.addoption(
        "--myVerbose",
        action="store",
        default=1,
        help="my verbose level"
    )
    parser.addoption(
        "--port",
        action="store",
        default=None,
        help="port to test"
    )


def line_separator(interrupter: str, symbol: str = "-", length: int = 136, color: int | None = None, colorAll: bool = False) -> str:
    if not interrupter:
        if color:
            return f"\033[{color}m" + symbol * (length//len(symbol)) + "\033[0m"
        return symbol * (length//len(symbol))
    interrupterNoColor = re.sub(r'\033\[[0-9;]*m', '', interrupter)
    side = (length - 2 - len(interrupterNoColor)) / 2
    if color:
        color = f"\033[{color}m"
        if colorAll:
            return color + symbol * math.ceil(side) + " " + interrupter + " " + symbol * math.floor(side) + "\033[0m"
        else:
            return color + symbol * math.ceil(side) + "\033[0m" + " " + interrupter + " " + color + symbol * math.floor(side) + "\033[0m"
    return symbol * math.ceil(side) + " " + interrupter + " " + symbol * math.floor(side)

def setup_logger(port):
    # set up fie location for output logs
    from config.paths import root_path
    log_folder = os.path.join(root_path,"Tests", "logs")
    os.makedirs(log_folder, exist_ok=True)
    from datetime import datetime
    timestamp = datetime.now().strftime("%m-%d-%Y__%H-%M-%S")
    subfolder = os.path.join(log_folder, timestamp)
    os.makedirs(subfolder, exist_ok=True)
    log_file_path = os.path.join(subfolder, f"test_{port}.log")
    return Logger(port, "Test Printer", consoleLogger=None, fileLogger=log_file_path, showFile=False, showLevel=False)

# @pytest.hookimpl(tryfirst=True)
# def pytest_sessionstart(session) -> None:
#     for arg in session.config.invocation_params.args:
#         if not hasattr(session.config, "verbosity") and arg.startswith("--myVerbose="):
#             session.config.verbosity = int(arg.split("=")[1])
#         elif not hasattr(session.config, "port") and arg.startswith("--port="):
#             session.config.port = arg.split("=")[1]
#         elif not hasattr(session.config, "testLevel") and arg.startswith("--testLevel="):
#             session.config.testLevel = int(arg.split("=")[1])
#     if session.config.verbosity > 2:
#         session.config.verbosity = 2
#
#     session.config.start_time = time.time()
#     session.config.passed_count = 0
#     session.config.failed_count = 0
#     session.config.skipped_count = 0
#     session.config.xfailed_count = 0
#     session.config.xpassed_count = 0
#     session.config.failNames = []
#     session.config.fails = {}
#     session.config.logger = setup_logger(session.config.port)
#
#
#     if session.config.verbosity >= 0:
#         logger = session.config.logger
#         logger.logMessageOnly("\033[1m" + line_separator("test session starts", symbol="=") + "\033[0m")
#         verinfo = platform.python_version()
#         msg = f"platform {sys.platform} -- Python {verinfo}"
#         pypy_version_info = getattr(sys, "pypy_version_info", None)
#         if pypy_version_info:
#             verinfo = ".".join(map(str, pypy_version_info[:3]))
#             msg += f"[pypy-{verinfo}-{pypy_version_info[3]}]"
#         msg += f", pytest-{pytest.__version__}, pluggy-{pluggy.__version__}"
#         logger.logMessageOnly(msg)
#         logger.logMessageOnly(f"rootdir: {session.config.rootdir}")

def pytest_collection_modifyitems(session, config, items):
    # session.config.logger.logMessageOnly(f"\033[1m...collected {len(items)} items...")
    file_order = [
        "test_app.py",
        "test_fabricator_list.py",
        "test_device.py",
        "test_fabricator.py",
    ]

    def get_file_order(item):
        file_name = item.location[0]
        return file_order.index(file_name) if file_name in file_order else len(file_order)

    # Sort the items based on the file order
    items.sort(key=get_file_order)

# def pytest_sessionfinish(session, exitstatus) -> None:
#     session_duration = time.time() - session.config.start_time
#     passes  = session.config.passed_count
#     fails   = session.config.failed_count
#     skips   = session.config.skipped_count
#     xfails  = session.config.xfailed_count
#     xpasses = session.config.xpassed_count
#     logger  = session.config.logger
#
#     if hasattr(session.config, "_capturemanager"):
#         capture_manager = session.config._capturemanager
#         # Suspend capturing to retrieve the output
#         captured = capture_manager.read_global_and_disable()
#
#         # Print the captured stdout and stderr
#         logger.logMessageOnly("\nCaptured output during tests:\n")
#         logger.logMessageOnly(captured)
#
#         # Re-enable capture if needed for further use
#         capture_manager.resume_global_capture()
#
#     stats = []
#     if passes > 0: stats.append(f"\033[32m\033[1m{passes} passed")
#     if fails > 0: stats.append(f"\033[31m\033[1m{fails} failed")
#     if skips > 0: stats.append(f"\033[33m{skips} skipped")
#     if xfails > 0: stats.append(f"\033[33m{xfails} xfailed")
#     if xpasses > 0: stats.append(f"\031[33m{xpasses} xpassed")
#
#     if len(stats) > 0: summary = ", ".join(stats)
#     else: summary = "\033[33mno tests ran"
#
#     summary += f"\033[32m in {session_duration:.2f}s"
#     if session_duration > 3600:
#         summary += f" ({session_duration // 3600:02.0f}:{session_duration % 3600 // 60:02.0f}:{(session_duration % 60)//1:02.0f}.{(session_duration % 1).__round__(2) * 100 // 1:02.0f})"
#     elif session_duration > 60:
#         summary += f" ({session_duration // 60:02.0f}:{(session_duration % 60)//1:02.0f}.{(session_duration % 1).__round__(2) * 100 // 1:02.0f})"
#
#     if session.config.failed_count > 0:
#         headerText = "\n" + line_separator("FAILURES", symbol="=")
#         logger.logMessageOnly(headerText, logLevel=logger.ERROR)
#         for failTest in session.config.failNames:
#             logger.logMessageOnly(line_separator(failTest, symbol="_"), end="\n", logLevel=logger.ERROR)
#             if not hasattr(session.config.fails[failTest], "reprtraceback"):
#                 if not hasattr(session.config.fails[failTest], "longrepr"):
#                     if hasattr(session.config.fails[failTest], "errorstring"):
#                         logger.error(session.config.fails[failTest].errorstring)
#                     else:
#                         logger.error(session.config.fails[failTest])
#                 else:
#                     logger.error(session.config.fails[failTest].longrepr)
#             elif not hasattr(session.config.fails[failTest].reprtraceback, "reprentries"):
#                 logger.error(session.config.fails[failTest].reprtraceback)
#             else:
#                 logger.logException(session.config.fails[failTest].reprtraceback.reprentries)
#     logger.logMessageOnly("\n\033[32m" + line_separator(summary, symbol="="))
#
visited_modules = set()

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_protocol(item, nextitem):
    module_name = item.module.__name__
    if module_name not in visited_modules:
        visited_modules.add(module_name)
        item.config.terminalReporter.write("\n" + line_separator(item.module.__desc__(), symbol="-", length=item.config.terminalReporter._tw.fullwidth - 1), flush=True)
    yield
#
# @pytest.hookimpl(hookwrapper=True)
# def pytest_runtest_logreport(report):
#     verbosity = report.verbosity
#     yield
#     logger = report.logger
#     port = report.port
#     if (report.when == "setup" and not report.passed) or (report.when == "call"):
#         if port is None:
#             # Retrieve port from the test function if it's set as an attribute
#             port = os.getenv("PORT")
#
#         if verbosity == 0:
#             if report.passed:
#                 logger.info("\033[32m.\033[0m")
#             elif report.failed:
#                 logger.info("\033[31mF\033[0m")
#             elif report.skipped:
#                 logger.info("\033[33ms\033[0m")
#             elif hasattr(report, "xfailed") and report.xfailed:
#                 logger.info("\033[33mX\033[0m")
#             elif hasattr(report, "xpassed") and report.xpassed:
#                 logger.info("\033[31mx\033[0m")
#             else:
#                 logger.info(f"IDK what happened!?!?: {report}")
#         elif verbosity == 1:
#             loc = report.nodeid.split("::")[-1]
#             testString = f"{loc}[{port}]{' ' * (59 - len(loc) - len(str(port)) - 2)}"
#             if report.passed:
#                 logger.info(f"{testString} \033[32mPASSED\033[0m")
#             elif report.failed:
#                 logger.info(f"{testString} \033[31mFAILED\033[0m")
#             elif report.skipped:
#                 logger.info(f"{testString} \033[33mSKIPPED\033[0m")
#             elif hasattr(report, "xfailed") and report.xfailed:
#                 logger.info(f"{testString} \033[33mXFAILED\033[0m")
#             elif hasattr(report, "xpassed") and report.xpassed:
#                 logger.info(f"{testString} \033[31mXPASSED\033[0m")
#             else:
#                 logger.info(f"{testString} IDK what happened!?!?: {report}")
#         elif verbosity >= 2:
#             loc = report.nodeid
#             testString = f"{loc}[{port}]{' ' * (79 - len(loc) - len(str(port)) - 2)}"
#             if report.passed:
#                 logger.info(f"{testString} \033[32mPASSED\033[0m")
#             elif report.failed:
#                 logger.info(f"{testString} \033[31mFAILED\033[0m:\n\n")
#                 if not hasattr(report, "longrepr"):
#                     if hasattr(report, "errorstring"):
#                         logger.error(report.errorstring)
#                     else:
#                         logger.error(report)
#                 elif not hasattr(report.longrepr, "reprtraceback"):
#                     logger.error(report.longrepr)
#                 elif not hasattr(report.longrepr.reprtraceback, "reprentries"):
#                     logger.error(report.longrepr.reprtraceback)
#                 else:
#                     logger.logException(report.longrepr.reprtraceback.reprentries)
#                 logger.logException(report.longrepr.reprtraceback.reprentries)
#             elif report.skipped:
#                 logger.info(f"{testString} \033[33mSKIPPED\033[0m: {report.longrepr[-1].split('Skipped: ')[-1]}")
#             else:
#                 logger.info(f"{testString} IDK what happened!?!?: {report}")
#
# def pytest_collectreport(report):
#     if report.failed:
#         intLogger.logMessageOnly(f"Collection failed:", logLevel=intLogger.ERROR)
#         if not hasattr(report.longrepr, "reprtraceback"):
#             intLogger.logException(report.longrepr.longrepr)
#             return
#         if not hasattr(report.longrepr.reprtraceback, "reprentries"):
#             intLogger.logException(report.longrepr.reprtraceback)
#             return
#         else: intLogger.logException(report.longrepr.reprtraceback.reprentries)

def pytest_terminal_summary(terminalreporter: TerminalReporter, exitstatus, config):
    import time
    from _pytest.terminal import format_session_duration
    session_duration = time.time() - terminalreporter._sessionstarttime
    (parts, main_color) = terminalreporter.build_summary_stats_line()
    line_parts = []
    for text, markup in parts:
        with_markup = terminalreporter._tw.markup(text, **markup)
        line_parts.append(with_markup)
    msg = ", ".join(line_parts)
    main_markup = {main_color: True}
    duration = f" in {format_session_duration(session_duration)}"
    duration_with_markup = terminalreporter._tw.markup(duration, **main_markup)
    msg += duration_with_markup
    config.logger.logMessageOnly("\n" + line_separator(msg, symbol="=", length=terminalreporter._tw.fullwidth, color=terminalreporter._tw._esctable[main_color]))
