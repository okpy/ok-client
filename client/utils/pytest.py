"""Pytest utilities for the ok client."""
import pytest


class TestResultPlugin:
    """A pytest plugin to capture test results and filter doctest tracebacks."""
    def __init__(self):
        self.failed_test = None
        self.successful_tests = []
        self.stdout = None
        self.stderr = None

    def pytest_runtest_makereport(self, item, call):
        """Hook called after each test has run."""
        if call.when == "call":
            if call.excinfo is not None:
                # If the test failed, store the item and capture its output
                if call.excinfo.type != pytest.skip.Exception:
                    self.failed_test = item.nodeid
                    capmanager = item.config.pluginmanager.getplugin('capmanager')
                    if capmanager:
                        self.captured_stdout, self.captured_stderr = capmanager.readouterr()
            else:
                # Test passed, add to successful tests
                self.successful_tests.append(item.nodeid)

        # Create report and apply traceback filtering for doctests
        report = pytest.TestReport.from_item_and_call(item, call)

        # Filter doctest tracebacks by removing first two frames
        if (hasattr(report, 'longrepr') and report.longrepr and 
            'doctest' in str(type(item)).lower()):
            tb_lines = str(report.longrepr).split('\n')
            filtered_lines = []
            frame_count = 0
            skip_frame = False
            
            for line in tb_lines:
                if line.strip() == "Traceback (most recent call last):":
                    filtered_lines.append(line)
                elif line.strip().startswith('File "'):
                    frame_count += 1
                    skip_frame = frame_count <= 2
                    if not skip_frame:
                        filtered_lines.append(line)
                elif not skip_frame:
                    filtered_lines.append(line)
            
            report.longrepr = '\n'.join(filtered_lines)

        return report

    def has_failed_test(self):
        return self.failed_test is not None

    def get_successful_tests(self):
        return self.successful_tests


def run_pytest(pytest_args):
    """Invoke pytest with pytest-grader configured, forwarding arguments as needed."""
    capture_plugin = TestResultPlugin()
    pytest_args.extend(['-x'])  # Stop after first failed test
    pytest_args.extend(['-q'])  # Don't show system information
    pytest_args.extend(['--doctest-modules'])  # Run all doctests
    pytest_args.extend(['-p', 'pytest_grader']) # Add pytest-grader plugin

    pytest.main(pytest_args, plugins=[capture_plugin])
    return capture_plugin