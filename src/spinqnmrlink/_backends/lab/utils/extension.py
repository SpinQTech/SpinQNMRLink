# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
try:
    import pyqtgraph as pg
    from pyqtgraph.Qt import QtCore, QtWidgets
except ImportError:  # Plotting is optional for communication-only usage.
    pg = None
    QtCore = None
    QtWidgets = None
import os
from pathlib import Path
import numpy as np
from typing import List
from ..utils.pulse import Pulse
from spinqnmrlink._core.waveforms import WaveformGeneratorBase

colors = {
    'fidRe': '#4c78a8',
    'fidIm': '#f2a541',
    'fidMod': '#2a9d8f',
    'lorenz': '#5f6b76',
    'fftRe': '#4c78a8',
    'fftIm': '#f2a541',
    'fftMod': '#2a9d8f',
    'fftFit': '#5f6b76',
}


def _require_plotting():
    if pg is None or QtCore is None or QtWidgets is None:
        raise RuntimeError(
            "Plotting requires the optional dependencies pyqtgraph and PyQt5. "
            "Install them with: pip install pyqtgraph PyQt5"
        )


def choose_image_save_path(parent=None, default_name="experiment_result.png"):
    """Let the user choose whether and where to save the experiment image."""
    _require_plotting()
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
        parent,
        "Save experiment image",
        default_name,
        "PNG image (*.png);;JPEG image (*.jpg *.jpeg)",
    )
    return file_path or None


def _exponential_envelope_fit(x_values, y_values):
    """Return a conservative exponential trend for finite FID magnitude data."""
    x = np.asarray(x_values, dtype=float)
    y = np.abs(np.asarray(y_values, dtype=float))
    finite = np.isfinite(x) & np.isfinite(y)
    x = x[finite]
    y = y[finite]
    if len(x) < 8 or np.ptp(x) <= 0:
        return None

    order = np.argsort(x)
    x = x[order]
    y = y[order]
    tail_count = max(3, len(y) // 5)
    baseline = float(np.median(y[-tail_count:]))
    signal = y - baseline
    peak = float(np.max(signal)) if signal.size else 0.0
    if peak <= 0:
        return None

    mask = signal > max(peak * 0.05, 1e-12)
    if int(np.count_nonzero(mask)) < 3:
        return None

    slope, intercept = np.polyfit(x[mask], np.log(signal[mask]), 1)
    if not np.isfinite(slope) or not np.isfinite(intercept) or slope >= 0:
        return None

    dense_x = np.linspace(float(x.min()), float(x.max()), 500)
    dense_y = baseline + np.exp(intercept + slope * dense_x)
    return dense_x, dense_y

def print_graph(
    result,
    window_title="Experiment Signal Result",
    validation_stem="signal_graph",
    on_shown=None,
):
    _require_plotting()
    # Get chart data
    if "graph" in result:
        graph_data = result["graph"]
    else:
        print("No graph data found")
        return

    # Some experiments may not return chart data at all. Avoid opening an empty
    # window and blocking on the Qt event loop in that case.
    if not graph_data:
        print("No chart points returned (graph is empty).")
        return

    # Create application and window
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    pg.setConfigOption('foreground', '#20242a')

    # Create main window
    main_window = QtWidgets.QWidget()
    main_window.setWindowTitle(window_title)
    main_window.resize(1200, 760)
    main_window.setStyleSheet(
        "QWidget { background-color: white; color: #20242a; }"
        "QComboBox, QPushButton { border: 1px solid #c7cdd3; border-radius: 3px; "
        "padding: 5px 9px; background-color: white; color: #20242a; }"
        "QPushButton:hover { background-color: #f2f5f7; }"
    )

    # Create main layout
    main_layout = QtWidgets.QVBoxLayout()
    main_layout.setContentsMargins(16, 14, 16, 16)
    main_layout.setSpacing(10)
    main_window.setLayout(main_layout)

    # Create control area
    control_layout = QtWidgets.QHBoxLayout()
    main_layout.addLayout(control_layout)

    # Create dropdown
    control_layout.addWidget(QtWidgets.QLabel("Data step:"))
    step_selector = QtWidgets.QComboBox()
    control_layout.addWidget(step_selector)
    control_layout.addStretch()
    save_button = QtWidgets.QPushButton("Save image...")
    control_layout.addWidget(save_button)

    # Fill dropdown options
    for i in range(len(graph_data)):
        step_selector.addItem(f"Step {i+1}")

    # Create chart area
    plot_layout = QtWidgets.QVBoxLayout()
    main_layout.addLayout(plot_layout)

    # Create plotting window
    win = pg.GraphicsLayoutWidget()
    plot_layout.addWidget(win)

    # Set window background to white
    win.setBackground('w')


    # Add two plotting areas
    p1 = win.addPlot()
    p1.setTitle("Time-Domain Signal (FID)", color="#20242a", size="12pt")
    win.nextRow()
    p2 = win.addPlot()
    p2.setTitle("Frequency-Domain Spectrum (FFT)", color="#20242a", size="12pt")

    # Set plot area labels
    p1.setLabel('left', 'Amplitude', color='#20242a')
    p1.setLabel('bottom', 'Time', units='ms', color='#20242a')
    # Set p1 to display grid
    p1.showGrid(x=True, y=True, alpha=0.12)
    p1.getAxis('bottom').setPen(pg.mkPen(color='k', width=1))
    p1.getAxis('left').setPen(pg.mkPen(color='k', width=1))
    p1.getAxis('bottom').setTextPen(pg.mkPen(color='#20242a'))
    p1.getAxis('left').setTextPen(pg.mkPen(color='#20242a'))
    p2.setLabel('left', 'Amplitude', color='#20242a')
    p2.setLabel('bottom', 'Frequency', units='Hz', color='#20242a')
    # Set p2 to display grid
    p2.showGrid(x=True, y=True, alpha=0.12)
    p2.getAxis('bottom').setPen(pg.mkPen(color='k', width=1))
    p2.getAxis('left').setPen(pg.mkPen(color='k', width=1))
    p2.getAxis('bottom').setTextPen(pg.mkPen(color='#20242a'))
    p2.getAxis('left').setTextPen(pg.mkPen(color='#20242a'))

    # Add legend
    p1_legend = p1.addLegend(labelTextColor='#20242a')
    p2_legend = p2.addLegend(labelTextColor='#20242a')

    # Define function to update chart
    def update_plot(index):
        # Clear existing charts
        p1.clear()
        p2.clear()

        # Keep one legend per plot instead of stacking a new legend per step.
        p1_legend.clear()
        p2_legend.clear()

        # Get selected step data
        step_data = graph_data[index]

        # Extract different types of chart data
        fftRe, fftIm, fftMod, fftFit, fidRe, fidIm, fidMod, lorenz = [], [], [], [], [], [], [], []

        for chart_name, points in step_data.items():
            if chart_name == "fftRe":
                fftRe = points
            elif chart_name == "fftIm":
                fftIm = points
            elif chart_name == "fftMod":
                fftMod = points
            elif chart_name == "fftFit":
                fftFit = points
            elif chart_name == "fidRe":
                fidRe = points
            elif chart_name == "fidIm":
                fidIm = points
            elif chart_name == "fidMod":
                fidMod = points
            elif chart_name == "lorenz":
                lorenz = points

        # Plot FID data. A Lorentzian is a frequency-domain peak model and is
        # therefore plotted below on the spectrum axis.
        if fidRe:
            x_fid = np.array([point[0] for point in fidRe])
            y_fid_re = np.array([point[1] for point in fidRe])
            p1.plot(x_fid, y_fid_re, pen=pg.mkPen(color=colors['fidRe'], width=1), name='FID real')

        if fidIm:
            x_fid = np.array([point[0] for point in fidIm])
            y_fid_im = np.array([point[1] for point in fidIm])
            p1.plot(x_fid, y_fid_im, pen=pg.mkPen(color=colors['fidIm'], width=1), name='FID imaginary')

        if fidMod:
            x_fid = np.array([point[0] for point in fidMod])
            y_fid_mod = np.array([point[1] for point in fidMod])
            p1.plot(x_fid, y_fid_mod, pen=pg.mkPen(color=colors['fidMod'], width=1), name='FID magnitude')
            envelope = _exponential_envelope_fit(x_fid, y_fid_mod)
            if envelope is not None:
                p1.plot(
                    envelope[0], envelope[1],
                    pen=pg.mkPen(
                        color=colors['lorenz'],
                        width=1,
                        style=QtCore.Qt.PenStyle.DashLine,
                    ),
                    name='Exponential envelope fit',
                )

        # Plot FFT data
        if fftRe:
            x_fft = np.array([point[0] for point in fftRe])
            y_fft_re = np.array([point[1] for point in fftRe])
            p2.plot(x_fft, y_fft_re, pen=pg.mkPen(color=colors['fftRe'], width=1), name='FFT real')

        if fftIm:
            x_fft = np.array([point[0] for point in fftIm])
            y_fft_im = np.array([point[1] for point in fftIm])
            p2.plot(x_fft, y_fft_im, pen=pg.mkPen(color=colors['fftIm'], width=1), name='FFT imaginary')

        if fftMod:
            x_fft = np.array([point[0] for point in fftMod])
            y_fft_mod = np.array([point[1] for point in fftMod])
            p2.plot(x_fft, y_fft_mod, pen=pg.mkPen(color=colors['fftMod'], width=1), name='FFT magnitude')

        if fftFit:
            x_fft = np.array([point[0] for point in fftFit])
            y_fft_fit = np.array([point[1] for point in fftFit])
            p2.plot(x_fft, y_fft_fit, pen=pg.mkPen(color=colors['fftFit'], width=1), name='FFT fit')

        if lorenz:
            x_lorenz = np.array([point[0] for point in lorenz])
            y_lorenz = np.array([point[1] for point in lorenz])
            p2.plot(x_lorenz, y_lorenz, pen=pg.mkPen(color=colors['lorenz'], width=1), name='Lorentzian fit')

    # Connect dropdown signal to update function
    step_selector.currentIndexChanged.connect(update_plot)

    def save_image():
        file_path = choose_image_save_path(main_window)
        if not file_path:
            return
        if not main_window.grab().save(file_path):
            QtWidgets.QMessageBox.warning(
                main_window, "Save failed", f"Could not save the image to:\n{file_path}"
            )

    save_button.clicked.connect(save_image)

    # If there is data, initialize chart
    if graph_data:
        update_plot(0)

    # Show main window
    main_window.show()
    if on_shown is not None:
        # Defer terminal interaction until Qt has made the chart visible.
        QtCore.QTimer.singleShot(0, on_shown)

    validation_dir = os.environ.get("SPINQLABLINK_VALIDATION_DIR")
    if validation_dir:
        output_path = Path(validation_dir) / f"{validation_stem}.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        def capture_and_close():
            main_window.grab().save(str(output_path))
            main_window.close()

        QtCore.QTimer.singleShot(700, capture_and_close)

    print("Chart data plotting completed")
    app.exec_()

def parse_spinq_file(pulses: List[Pulse], file_path: str):
    try:
        with open(file_path, "r") as file:
            file_dict = file.read()

        # Parse pulse file content
        import json
        file_dict = json.loads(file_dict)
        pulses_dict = file_dict["pulse"]

        # Parse hydrogen channel pulses
        for pulse in pulses_dict["channel1_pulse"]:
            pulses.append(Pulse(
                path=0,  # Hydrogen channel
                width=pulse.get("width", 0),
                amplitude=pulse.get("amplitude", 0.0),
                phase=pulse.get("phase", 0.0),
                detuning=pulse.get("detuning", 0.0)
            ))

        # Parse phosphorus channel pulses
        for pulse in pulses_dict["channel2_pulse"]:
            pulses.append(Pulse(
                path=1,  # Phosphorus channel
                width=pulse.get("width", 0),
                amplitude=pulse.get("amplitude", 0.0),
                phase=pulse.get("phase", 0.0),
                detuning=pulse.get("detuning", 0.0)
            ))
    except FileNotFoundError:
        print(f"could not find pulse file: {file_path}")
    except json.JSONDecodeError:
        print("pulse file format error, could not parse JSON content")
    except Exception as e:
        print(f"error: {str(e)}")

def pulse_domain_analysis(pulses: List[Pulse]):
    _require_plotting()
    """
    Analyze the domain characteristics of a pulse sequence and compute
    the Fourier transform from the time domain to the frequency domain.

    Args:
        pulses: List of pulse sequences.

    Returns:
        A dictionary containing the frequency-domain analysis results,
        including frequency, real part, imaginary part, and magnitude.
    """
    import numpy as np
    from numpy.fft import fft, fftshift
    import math

    if not pulses:
        return {
            "freqs": [],
            "real": [],
            "imag": [],
            "magnitude": []
        }

    # Extract pulse parameters
    amps = [p.amplitude for p in pulses]
    phases = [p.phase for p in pulses]
    durations = [p.width for p in pulses]
    channels = [p.path for p in pulses]
    detunings = [p.detuning for p in pulses]

    max_amp = max(amps) if amps else 1.0
    sample_points = 64  # Number of sampling points

    # Compute total time interval
    total_duration = sum(durations)
    t_total = []
    pulse_signals = []
    pulse_signals_norm = []

    # Generate time-domain signal for each pulse
    for i, pulse in enumerate(pulses):
        t_init = sum(durations[:i])
        t_end = t_init + durations[i]
        dt = (t_end - t_init) / sample_points

        for j in range(sample_points):
            t = t_init + j * dt
            t_total.append(t)

            # Generate complex-valued pulse signal
            if amps[i] == 0:
                pulse_signals.append(complex(0, 0))
                pulse_signals_norm.append(complex(0, 0))
            else:
                # Compute phase (degrees to radians)
                phase_rad = phases[i] / 360.0 * 2 * math.pi
                # Compute frequency (considering detuning)
                freq = detunings[i]

                # Generate complex signal
                real_part = amps[i] * math.cos(2 * math.pi * freq * t + phase_rad)
                imag_part = amps[i] * math.sin(2 * math.pi * freq * t + phase_rad)

                pulse_signals.append(complex(real_part, imag_part))
                pulse_signals_norm.append(complex(real_part / max_amp, imag_part / max_amp))

    # Pad signal length to a power of 2 to improve FFT efficiency
    length = 2 ** math.ceil(math.log2(len(pulse_signals) * 5))

    # If there is no valid data, return an empty result
    if length == 0:
        return {
            "freqs": [],
            "real": [],
            "imag": [],
            "mod": []
        }

    # Zero-pad to the specified length
    pulse_signals = np.pad(pulse_signals, (0, length - len(pulse_signals)), 'constant')
    pulse_signals_norm = np.pad(pulse_signals_norm, (0, length - len(pulse_signals_norm)), 'constant')

    # Perform FFT
    fft_result = fft(pulse_signals)
    fft_result_norm = fft(pulse_signals_norm)

    # Compute frequency axis
    fs = sample_points / t_total[-1] if t_total else 1.0
    f = np.array([(i - length/2) * fs / length for i in range(length)])

    # Shift zero-frequency component to the center
    fft_result = fftshift(fft_result)
    fft_result_norm = fftshift(fft_result_norm)

    # Define the frequency range of interest
    freq_range = int(length * 0.1)  # Take the central 10% range

    start_idx = length // 2 - freq_range
    end_idx = length // 2 + freq_range

    # Extract data in the specified range
    freqs = f[start_idx:end_idx].tolist()
    fft_selected = fft_result[start_idx:end_idx]
    fft_norm_selected = fft_result_norm[start_idx:end_idx]

    # Compute magnitudes
    magnitudes = [abs(x) for x in fft_selected]
    norm_factor = max(magnitudes) / (length * 2) if magnitudes else 1.0
    norm_factor = 1.0 if norm_factor == 0 else norm_factor

    # Build result
    result = {
        "freqs": freqs,
        "real": [(x.real / (length * 2) / norm_factor) for x in fft_selected],
        "imag": [(x.imag / (length * 2) / norm_factor) for x in fft_selected],
        "mod": [(abs(x) / (length * 2) / norm_factor) for x in fft_selected]
    }

    # Display spectrum plot
    app = QtWidgets.QApplication([])

    # Create main window
    main_window = QtWidgets.QWidget()
    main_window.setWindowTitle("Pulse Spectrum Analysis")
    main_window.resize(800, 500)

    # Create main layout
    main_layout = QtWidgets.QVBoxLayout()
    main_window.setLayout(main_layout)

    # Create plotting area
    win = pg.GraphicsLayoutWidget()
    main_layout.addWidget(win)
    win.setBackground('w')

    # Add plotting area
    p1 = win.addPlot(title="Spectrum Analysis")
    p1.setLabel('left', 'Amplitude')
    p1.setLabel('bottom', 'Frequency (Hz)')

    # Plot spectrum
    p1.plot(result["freqs"], result["mod"], pen=pg.mkPen(color=colors['fftMod'], width=1), name='FFT Magnitude')
    p1.plot(result["freqs"], result["real"], pen=pg.mkPen(color=colors['fftRe'], width=1), name='FFT Real')
    p1.plot(result["freqs"], result["imag"], pen=pg.mkPen(color=colors['fftIm'], width=1), name='FFT Imaginary')

    # Show window
    main_window.show()
    app.exec_()


class WaveformGenerator(WaveformGeneratorBase):
    """SpinQLabLink-compatible facade over the shared waveform algorithm."""

    pulse_type = Pulse
