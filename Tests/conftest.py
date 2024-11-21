import math
import os
import platform
import re
import sys
import time
import pluggy
import pytest
from app import fabricator_list

@pytest.fixture(scope="session")
def fabricator(request, app):
    port = request.session.config.port
    if not port: return None
    from serial.tools.list_ports_common import ListPortInfo
    from serial.tools.list_ports_linux import SysFS
    if isinstance(port, str):
        fabricator = fabricator_list.getFabricatorByPort(port)
    elif isinstance(port, ListPortInfo) or isinstance(port, SysFS):
        fabricator = fabricator_list.getFabricatorByPort(port.device)
    else:
        fabricator = None
    if fabricator is None:
        pytest.skip("No port specified")
    if os.getenv("LEVEL") == "DEBUG":
        fabricator.device.logger.setLevel(fabricator.device.logger.DEBUG)
    fabricator.device.connect()
    yield fabricator
    fabricator.device.disconnect()

@pytest.fixture(scope="session")
def app():
    from app import app
    app = app
    with app.app_context():
        yield app
        fabricator_list.teardown()


from Classes.Logger import Logger

intLogger = Logger("Internal Errors", consoleLogger=sys.stdout, fileLogger="internal_errors.log", loggingLevel=Logger.INFO)

def pytest_internalerror(excrepr, excinfo):
    # This hook is called when pytest encounters an internal error
    intLogger.error(f"Internal pytest error:\n{excrepr}")

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

def line_separator(interrupter: str, symbol: str = "-", length: int = 136) -> str:
    if not interrupter:
        return symbol * (length//len(symbol))
    interrupterNoColor = re.sub(r'\033\[[0-9;]*m', '', interrupter)
    side = (length - 2 - len(interrupterNoColor)) / 2
    return symbol * math.ceil(side) + " " + interrupter + " " + symbol * math.floor(side)

def setup_logger(port):
    # set up fie location for output logs
    log_folder = "logs"
    os.makedirs(log_folder, exist_ok=True)
    from datetime import datetime
    timestamp = datetime.now().strftime("%m-%d-%Y__%H-%M-%S")
    subfolder = os.path.join(log_folder, timestamp)
    os.makedirs(subfolder, exist_ok=True)
    log_file_path = os.path.join(subfolder, f"test_{port}.log")
    return Logger(port, "Test Printer", consoleLogger=sys.stdout, fileLogger=log_file_path, showFile=False, showLevel=False)

@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session) -> None:
    for arg in session.config.invocation_params.args:
        if not hasattr(session.config, "verbosity") and arg.startswith("--myVerbose="):
            session.config.verbosity = int(arg.split("=")[1])
        elif not hasattr(session.config, "port") and arg.startswith("--port="):
            session.config.port = arg.split("=")[1]
        elif not hasattr(session.config, "testLevel") and arg.startswith("--testLevel="):
            session.config.testLevel = int(arg.split("=")[1])
    if session.config.verbosity > 2:
        session.config.verbosity = 2

    session.config.start_time = time.time()
    session.config.passed_count = 0
    session.config.failed_count = 0
    session.config.skipped_count = 0
    session.config.xfailed_count = 0
    session.config.xpassed_count = 0
    session.config.failNames = []
    session.config.fails = {}
    session.config.logger = setup_logger(session.config.port)


    if session.config.verbosity >= 0:
        logger = session.config.logger
        logger.logMessageOnly("\033[1m" + line_separator("test session starts", symbol="=") + "\033[0m")
        verinfo = platform.python_version()
        msg = f"platform {sys.platform} -- Python {verinfo}"
        pypy_version_info = getattr(sys, "pypy_version_info", None)
        if pypy_version_info:
            verinfo = ".".join(map(str, pypy_version_info[:3]))
            msg += f"[pypy-{verinfo}-{pypy_version_info[3]}]"
        msg += f", pytest-{pytest.__version__}, pluggy-{pluggy.__version__}"
        logger.logMessageOnly(msg)
        logger.logMessageOnly(f"rootdir: {session.config.rootdir}")

def pytest_collection_modifyitems(session, config, items):
    session.config.logger.logMessageOnly(f"\033[1m...collected {len(items)} items...")
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

def pytest_sessionfinish(session, exitstatus) -> None:
    session_duration = time.time() - session.config.start_time
    passes  = session.config.passed_count
    fails   = session.config.failed_count
    skips   = session.config.skipped_count
    xfails  = session.config.xfailed_count
    xpasses = session.config.xpassed_count
    logger  = session.config.logger

    if hasattr(session.config, "_capturemanager"):
        capture_manager = session.config._capturemanager
        # Suspend capturing to retrieve the output
        captured = capture_manager.read_global_and_disable()

        # Print the captured stdout and stderr
        logger.logMessageOnly("\nCaptured output during tests:\n")
        logger.logMessageOnly(captured)

        # Re-enable capture if needed for further use
        capture_manager.resume_global_capture()

    stats = []
    if passes > 0: stats.append(f"\033[32m\033[1m{passes} passed")
    if fails > 0: stats.append(f"\033[31m\033[1m{fails} failed")
    if skips > 0: stats.append(f"\033[33m{skips} skipped")
    if xfails > 0: stats.append(f"\033[33m{xfails} xfailed")
    if xpasses > 0: stats.append(f"\031[33m{xpasses} xpassed")

    if len(stats) > 0: summary = ", ".join(stats)
    else: summary = "\033[33mno tests ran"

    summary += f"\033[32m in {session_duration:.2f}s"
    if session_duration > 3600:
        summary += f" ({session_duration // 3600:02.0f}:{session_duration % 3600 // 60:02.0f}:{(session_duration % 60)//1:02.0f}.{(session_duration % 1).__round__(2) * 100 // 1:02.0f})"
    elif session_duration > 60:
        summary += f" ({session_duration // 60:02.0f}:{(session_duration % 60)//1:02.0f}.{(session_duration % 1).__round__(2) * 100 // 1:02.0f})"

    if session.config.failed_count > 0:
        headerText = "\n" + line_separator("FAILURES", symbol="=")
        logger.logMessageOnly(headerText, logLevel=logger.ERROR)
        for failTest in session.config.failNames:
            logger.logMessageOnly(line_separator(failTest, symbol="_"), end="\n", logLevel=logger.ERROR)
            if not hasattr(session.config.fails[failTest], "reprtraceback"):
                if not hasattr(session.config.fails[failTest], "longrepr"):
                    if hasattr(session.config.fails[failTest], "errorstring"):
                        logger.error(session.config.fails[failTest].errorstring)
                    else:
                        logger.error(session.config.fails[failTest])
                else:
                    logger.error(session.config.fails[failTest].longrepr)
            elif not hasattr(session.config.fails[failTest].reprtraceback, "reprentries"):
                logger.error(session.config.fails[failTest].reprtraceback)
            else:
                logger.logException(session.config.fails[failTest].reprtraceback.reprentries)
    logger.logMessageOnly("\n\033[32m" + line_separator(summary, symbol="="))

visited_modules = set()

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()  # Retrieve the TestReport object
    # Only check the outcome after the "call" phase (i.e., after the test ran)
    if (report.when == "setup" and not report.passed) or (report.when == "call"):
        if report.passed:
            if hasattr(report, "wasxfail"):
                report.outcome = "xpassed"
                report.xpassed = True
                item.config.xpassed_count += 1
            else:
                item.config.passed_count += 1
        elif report.failed:
            item.config.failed_count += 1
            failName = report.nodeid.split("::")[1] + "." + item.name
            item.config.failNames.append(failName)
            item.config.fails[failName] = report.longrepr
        elif report.skipped:
            if hasattr(report, "wasxfail"):
                report.outcome = "xfailed"
                report.xfailed = True
                item.config.xfailed_count += 1
            else:
                item.config.skipped_count += 1
    report.port = item.config.port
    report.verbosity = item.config.verbosity
    report.logger = item.config.logger
    module_name = item.module.__name__
    if module_name not in visited_modules:
        visited_modules.add(module_name)
        report.logger.logMessageOnly("\n" + line_separator(item.module.__desc__(), symbol="-"))

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_logreport(report):
    verbosity = report.verbosity
    yield
    logger = report.logger
    port = report.port
    if (report.when == "setup" and not report.passed) or (report.when == "call"):
        if port is None:
            # Retrieve port from the test function if it's set as an attribute
            port = os.getenv("PORT")

        if verbosity == 0:
            if report.passed:
                logger.info("\033[32m.\033[0m")
            elif report.failed:
                logger.info("\033[31mF\033[0m")
            elif report.skipped:
                logger.info("\033[33ms\033[0m")
            elif hasattr(report, "xfailed") and report.xfailed:
                logger.info("\033[33mX\033[0m")
            elif hasattr(report, "xpassed") and report.xpassed:
                logger.info("\033[31mx\033[0m")
            else:
                logger.info(f"IDK what happened!?!?: {report}")
        elif verbosity == 1:
            loc = report.nodeid.split("::")[-1]
            testString = f"{loc}[{port}]{' ' * (59 - len(loc) - len(str(port)) - 2)}"
            if report.passed:
                logger.info(f"{testString} \033[32mPASSED\033[0m")
            elif report.failed:
                logger.info(f"{testString} \033[31mFAILED\033[0m")
            elif report.skipped:
                logger.info(f"{testString} \033[33mSKIPPED\033[0m")
            elif hasattr(report, "xfailed") and report.xfailed:
                logger.info(f"{testString} \033[33mXFAILED\033[0m")
            elif hasattr(report, "xpassed") and report.xpassed:
                logger.info(f"{testString} \033[31mXPASSED\033[0m")
            else:
                logger.info(f"{testString} IDK what happened!?!?: {report}")
        elif verbosity >= 2:
            loc = report.nodeid
            testString = f"{loc}[{port}]{' ' * (79 - len(loc) - len(str(port)) - 2)}"
            if report.passed:
                logger.info(f"{testString} \033[32mPASSED\033[0m")
            elif report.failed:
                logger.info(f"{testString} \033[31mFAILED\033[0m:\n\n")
                if not hasattr(report, "longrepr"):
                    if hasattr(report, "errorstring"):
                        logger.error(report.errorstring)
                    else:
                        logger.error(report)
                elif not hasattr(report.longrepr, "reprtraceback"):
                    logger.error(report.longrepr)
                elif not hasattr(report.longrepr.reprtraceback, "reprentries"):
                    logger.error(report.longrepr.reprtraceback)
                else:
                    logger.logException(report.longrepr.reprtraceback.reprentries)
                logger.logException(report.longrepr.reprtraceback.reprentries)
            elif report.skipped:
                logger.info(f"{testString} \033[33mSKIPPED\033[0m: {report.longrepr[-1].split('Skipped: ')[-1]}")
            else:
                logger.info(f"{testString} IDK what happened!?!?: {report}")

def pytest_collectreport(report):
    if report.failed:
        intLogger.logMessageOnly(f"Collection failed:", logLevel=intLogger.ERROR)
        if not hasattr(report.longrepr, "reprtraceback"):
            intLogger.logException(report.longrepr.longrepr)
            return
        if not hasattr(report.longrepr.reprtraceback, "reprentries"):
            intLogger.logException(report.longrepr.reprtraceback)
            return
        else: intLogger.logException(report.longrepr.reprtraceback.reprentries)