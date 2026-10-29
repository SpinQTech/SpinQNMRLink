import threading
import time
from types import SimpleNamespace

import pytest

from spinqnmrlink import (
    DeviceNotReadyError,
    ExperimentFailedError,
    ExperimentRejectedError,
    ExperimentTerminatedError,
    ExperimentTimeoutError,
    LabDevice,
    LabSettings,
    ModeMismatchError,
    SDKSettings,
    SpinQNMRLink,
    SubmissionOutcomeUnknownError,
    TriangulumSettings,
)


class FakeBackend:
    """Deterministic unit-test double, not simulated measurement evidence."""

    def __init__(self, mode="TWO", states=("COMPLETED",), response=True):
        self.mode = SimpleNamespace(name=mode)
        self.connection_state = SimpleNamespace(name="READY")
        self.is_logged_in = True
        self.connected = True
        self.states = iter(states)
        self.last_state = "PENDING"
        self.response = response
        self.expMgr = SimpleNamespace(current_experiment_params=None)
        self.sent = 0
        self.deregistered = 0
        self.closed = 0

    def get_connection(self):
        return self.connected

    def get_qubit_mode(self):
        return self.mode

    def get_expMgr(self, **kwargs):
        return self.expMgr

    def register_experiment(self, kind, **kwargs):
        self.experiment = SimpleNamespace(id="unit-test-task", parameters=None)
        return self.experiment, None

    def run_experiment(self, **kwargs):
        self.sent += 1
        return 1

    def wait_for_request_response(self, sequence_id, **kwargs):
        if isinstance(self.response, Exception):
            raise self.response
        return SimpleNamespace(success=self.response, raw_code=0 if self.response else 9)

    def get_experiment_status(self, **kwargs):
        self.last_state = next(self.states, self.last_state)
        return self.last_state

    def get_experiment_result(self, **kwargs):
        assert self.last_state == "COMPLETED"
        return {"result": {"real": 0.5}, "state": "COMPLETED"}

    def deregister_experiment(self, **kwargs):
        self.deregistered += 1

    def disconnect(self, **kwargs):
        self.closed += 1
        self.connected = False


def device_with(fake):
    device = LabDevice(LabSettings(host="localhost", port=8181, account="test", password="test"))
    device._client = fake
    return device


def test_completed_result_retains_raw_metadata_and_cleans_registration():
    fake = FakeBackend()
    device = device_with(fake)
    result = device.create_experiment("lab.two.rabi").run(timeout=1)
    assert result.status == "COMPLETED" and result.data == {"real": 0.5}
    assert result.task_id == "unit-test-task"
    assert result.metadata["parameters"]["pulses"][0]["width_us"] == 40
    assert fake.sent == 1 and fake.deregistered == 1
    assert "password" not in result.to_json()


@pytest.mark.parametrize(
    "status,error",
    [
        ("FAILED", ExperimentFailedError),
        ("TERMINATED", ExperimentTerminatedError),
        ("TIMEOUT", ExperimentFailedError),
    ],
)
def test_remote_failures_are_not_completed(status, error):
    fake = FakeBackend(states=(status,))
    with pytest.raises(error):
        device_with(fake).create_experiment("lab.two.rabi").run(timeout=1)
    assert fake.deregistered == 1


def test_rejection_never_waits_for_measurement():
    fake = FakeBackend(response=False)
    with pytest.raises(ExperimentRejectedError):
        device_with(fake).create_experiment("lab.two.rabi").run(timeout=1)
    assert fake.last_state == "PENDING"


def test_timeout_retains_task_identity_and_blocks_accidental_replay():
    fake = FakeBackend(states=("RUNNING",))
    device = device_with(fake)
    experiment = device.create_experiment("lab.two.rabi")
    with pytest.raises(ExperimentTimeoutError) as caught:
        experiment.run(timeout=0.01)
    assert caught.value.task_id == "unit-test-task"
    with pytest.raises(SubmissionOutcomeUnknownError):
        experiment.run(timeout=1)
    assert fake.sent == 1


class ScheduledBackend(FakeBackend):
    """Advance a local clock to known remote state observations without sleeping."""

    def __init__(self, timeline, clock):
        super().__init__()
        self.timeline = iter(timeline)
        self.clock = clock

    def get_experiment_status(self, **kwargs):
        self.clock.seconds, self.last_state = next(self.timeline)
        return self.last_state


def install_task_clock(monkeypatch):
    import spinqnmrlink.experiments as module

    clock = SimpleNamespace(seconds=0.0)
    monkeypatch.setattr(module, "time", SimpleNamespace(
        monotonic=lambda: clock.seconds, sleep=lambda _: None))
    return clock


def test_queue_does_not_consume_execution_timeout_and_metadata_separates_phases(monkeypatch):
    clock = install_task_clock(monkeypatch)
    fake = ScheduledBackend([(0, "PENDING"), (600, "RUNNING"), (700, "COMPLETED")], clock)
    result = device_with(fake).create_experiment("lab.two.rabi").run(timeout=300)
    assert result.metadata["queue_duration_seconds"] == 600
    assert result.metadata["execution_duration_seconds"] == 100
    assert result.metadata["execution_started_at_utc"] is not None
    assert result.metadata["submitted_at_utc"] == result.metadata["started_at_utc"]
    assert result.metadata["acknowledged_at_utc"] is not None
    assert fake.sent == 1 and fake.deregistered == 1


@pytest.mark.parametrize("phase,timeline,queue_timeout", (
    ("queue", [(601, "PENDING")], 600),
    ("execution", [(600, "RUNNING"), (901, "RUNNING")], None),
))
def test_queue_and_execution_timeout_retain_identity_without_replay(
    monkeypatch, phase, timeline, queue_timeout
):
    clock = install_task_clock(monkeypatch)
    fake = ScheduledBackend(timeline, clock)
    device = device_with(fake)
    experiment = device.create_experiment("lab.two.rabi")
    with pytest.raises(ExperimentTimeoutError) as caught:
        experiment.run(timeout=300, queue_timeout=queue_timeout)
    assert caught.value.phase == phase
    assert caught.value.task_id == "unit-test-task"
    with pytest.raises(SubmissionOutcomeUnknownError):
        experiment.run(timeout=300)
    assert fake.sent == 1


def test_started_before_ack_keeps_original_execution_deadline(monkeypatch):
    clock = install_task_clock(monkeypatch)
    fake = ScheduledBackend([(102, "RUNNING")], clock)

    def acknowledge(sequence_id, timeout):
        assert timeout == 10  # request_timeout is independent of the execution budget.
        clock.seconds = 100
        fake.experiment.execution_started_monotonic = 50
        fake.experiment.execution_started_at_utc = "2026-10-27T00:00:50+00:00"
        return SimpleNamespace(success=True)

    fake.wait_for_request_response = acknowledge
    with pytest.raises(ExperimentTimeoutError) as caught:
        device_with(fake).create_experiment("lab.two.rabi").run(timeout=51)
    assert caught.value.phase == "execution"


def test_completion_without_start_does_not_fabricate_execution_time():
    result = device_with(FakeBackend()).create_experiment("lab.two.rabi").run(timeout=1)
    assert result.metadata["execution_started_at_utc"] is None
    assert result.metadata["execution_duration_seconds"] is None
    assert result.metadata["queue_duration_seconds"] is None


@pytest.mark.parametrize("queue_timeout", (0, -1, True, float("inf")))
def test_invalid_queue_timeout_is_rejected_before_submission(queue_timeout):
    fake = FakeBackend()
    with pytest.raises(ValueError):
        device_with(fake).create_experiment("lab.two.rabi").run(timeout=1, queue_timeout=queue_timeout)
    assert fake.sent == 0


def test_observer_close_drains_already_queued_notifications_within_budget():
    from spinqnmrlink._backends.lab.connection.events import OrderedCallbackDispatcher

    entered, release, notified = threading.Event(), threading.Event(), threading.Event()
    dispatcher = OrderedCallbackDispatcher()

    def first(_):
        entered.set()
        release.wait(2)

    try:
        dispatcher.submit(first, None)
        assert entered.wait(1)
        dispatcher.submit(lambda _: notified.set(), None)
        assert not dispatcher.close(timeout=0.01)
        release.set()
        assert dispatcher.close(timeout=1)
        assert notified.is_set()
    finally:
        release.set()
        dispatcher.close(timeout=1)


def test_disconnect_observer_and_caller_can_close_concurrently_without_lock_inversion():
    fake = FakeBackend()
    device = device_with(fake)
    entered, close_started, callback_done = threading.Event(), threading.Event(), threading.Event()
    errors = []
    disconnect = fake.disconnect

    def close_backend(**kwargs):
        close_started.set()
        disconnect(**kwargs)

    fake.disconnect = close_backend

    def observer(_):
        entered.set()
        assert close_started.wait(1)
        try:
            device.close(timeout=1)
        except Exception as error:
            errors.append(error)
        callback_done.set()

    device.subscribe_disconnect(observer)
    device._record_disconnect(0, fake, "peer reset", {})
    try:
        assert entered.wait(1)
        device.close(timeout=0.3)
        assert callback_done.wait(1)
        assert errors == []
    finally:
        close_started.set()
        device.close(timeout=1)


def test_lost_acknowledgement_is_unknown_and_not_retried():
    from spinqnmrlink._backends.lab.connection.request import RequestResponseTimeoutError

    fake = FakeBackend(response=RequestResponseTimeoutError("unit test"))
    device = device_with(fake)
    with pytest.raises(SubmissionOutcomeUnknownError):
        device.create_experiment("lab.two.rabi").run(timeout=1)
    assert fake.sent == 1 and fake.deregistered == 1


def test_offline_and_mode_mismatch_send_nothing():
    fake = FakeBackend(mode="THREE")
    device = device_with(fake)
    with pytest.raises(ModeMismatchError):
        device.create_experiment("lab.two.rabi").run(timeout=1)
    fake.connected = False
    with pytest.raises(DeviceNotReadyError):
        device.create_experiment("lab.three.circuit").run(timeout=1)
    assert fake.sent == 0


def test_one_device_failure_does_not_change_the_other_and_sdk_closes_both():
    settings = dict(host="localhost", port=8181, account="test", password="test")
    with SpinQNMRLink(
        SDKSettings(lab=LabSettings(**settings), triangulum=TriangulumSettings(**settings))
    ) as sdk:
        left, right = FakeBackend(response=False), FakeBackend()
        sdk.device("lab")._client = left
        sdk.device("triangulum")._client = right
        with pytest.raises(ExperimentRejectedError):
            sdk.device("lab").create_experiment("lab.two.rabi").run(timeout=1)
        assert sdk.device("triangulum").is_ready
    assert left.closed == right.closed == 1
    sdk.close()
    assert left.closed == right.closed == 1


def test_device_concurrency_lock_rejects_a_second_session():
    device = device_with(FakeBackend())
    device._run_lock.acquire()
    try:
        with pytest.raises(RuntimeError, match="one active"):
            device.create_experiment("lab.two.rabi").run(timeout=1)
    finally:
        device._run_lock.release()


def test_cleanup_failure_does_not_hide_submission_rejection():
    fake = FakeBackend(response=False)

    def broken_cleanup(**kwargs):
        raise RuntimeError("cleanup failed")

    fake.deregister_experiment = broken_cleanup
    device = device_with(fake)
    with pytest.raises(ExperimentRejectedError):
        device.create_experiment("lab.two.rabi").run(timeout=1)
    assert not device._run_lock.locked()


def test_mode_change_before_send_is_explicit_and_does_not_mark_task_as_sent():
    from spinqnmrlink._backends.lab.connection.request import QubitModeMismatchError

    fake = FakeBackend()

    def changed_mode(**kwargs):
        raise QubitModeMismatchError("unit test")

    fake.run_experiment = changed_mode
    device = device_with(fake)
    with pytest.raises(ModeMismatchError):
        device.create_experiment("lab.two.rabi").run(timeout=1)
    assert device._last_unresolved_task is None
    assert fake.sent == 0 and fake.deregistered == 1


def test_dispatcher_close_is_bounded_even_with_full_queue_and_blocked_observer():
    from spinqnmrlink._backends.lab.connection.events import OrderedCallbackDispatcher

    started, release = threading.Event(), threading.Event()
    dispatcher = OrderedCallbackDispatcher(maxsize=1)

    def callback(value):
        started.set()
        release.wait(1)

    dispatcher.submit(callback, None)
    assert started.wait(1)
    dispatcher.submit(callback, None)
    clock = time.monotonic()
    try:
        assert dispatcher.close(timeout=0.01) is False
        assert time.monotonic() - clock < 0.2
    finally:
        release.set()
        dispatcher._thread.join(1)
