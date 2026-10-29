# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
try:
    import pyqtgraph as pg
    from pyqtgraph.Qt import QtWidgets
except ImportError:  # Plotting is optional for communication-only usage.
    pg = None
    QtWidgets = None
import numpy as np
from typing import List
from ..utils.pulse import Pulse
from spinqnmrlink._core.waveforms import WaveformGeneratorBase
from ..utils.logger import LoggerManager
import base64
import zlib
import json
import struct
from typing import Dict, List, Optional, Tuple, Any

logger = LoggerManager.get_logger(name='extension')
colors = {
    'fidRe': '#2557d5',     # Blue
    'fidIm': '#df265a',     # Red
    'fidMod': '#32325D',    # Green
    'lorenz': '#800000',    # Purple
    'fftRe': '#2557d5',     # Blue
    'fftIm': '#df265a',     # Red
    'fftMod': '#32325D',    # Green
    'fftFit': '#800000'     # Purple
}


def _require_plotting():
    if pg is None or QtWidgets is None:
        raise RuntimeError(
            "Plotting requires the optional dependencies pyqtgraph and PyQt5. "
            "Install them with: pip install pyqtgraph PyQt5"
        )

def print_graph(result):
    _require_plotting()
    # Get chart data
    if "graph" in result:
        graph_data = process_experiment_graph(result["graph"])
    else:
        logger.error("No graph data found")
        return

    # Create application and window
    app = QtWidgets.QApplication([])

    # Create main window
    main_window = QtWidgets.QWidget()
    main_window.setWindowTitle("Experiment Signal Result")
    main_window.resize(1200, 700)

    # Create main layout
    main_layout = QtWidgets.QVBoxLayout()
    main_window.setLayout(main_layout)

    # Create control area
    control_layout = QtWidgets.QHBoxLayout()
    main_layout.addLayout(control_layout)

    # Create dropdown
    control_layout.addWidget(QtWidgets.QLabel("Select Step Data:"))
    step_selector = QtWidgets.QComboBox()
    control_layout.addWidget(step_selector)
    control_layout.addStretch()  # Add elastic space to left-align controls

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
    p1 = win.addPlot(title="FID Signal and Lorenz Fitting")
    win.nextRow()
    p2 = win.addPlot(title="FFT Spectrum")

    # Set plot area labels
    p1.setLabel('left', 'Amplitude')
    p1.setLabel('bottom', 'Time (ms) / Frequency (Hz)')
    # Set p1 to display grid
    p1.showGrid(x=True, y=True, alpha=0.2)
    p1.getAxis('bottom').setPen(pg.mkPen(color='k', width=1))
    p1.getAxis('left').setPen(pg.mkPen(color='k', width=1))
    p2.setLabel('left', 'Amplitude')
    p2.setLabel('bottom', 'Frequency (Hz)')
    # Set p2 to display grid
    p2.showGrid(x=True, y=True, alpha=0.2)
    p2.getAxis('bottom').setPen(pg.mkPen(color='k', width=1))
    p2.getAxis('left').setPen(pg.mkPen(color='k', width=1))

    # Add legend
    p1_legend = p1.addLegend()
    p2_legend = p2.addLegend()

    # Define function to update chart
    def update_plot(index):
        # Clear existing charts
        p1.clear()
        p2.clear()

        # Re-add legends
        p1_legend = p1.addLegend()
        p2_legend = p2.addLegend()

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

        # Plot FID data and Lorenz fitting curve
        if fidRe:
            x_fid = np.array([point[0] for point in fidRe])
            y_fid_re = np.array([point[1] for point in fidRe])
            p1.plot(x_fid, y_fid_re, pen=pg.mkPen(color=colors['fidRe'], width=1), name='FID Real')

        if fidIm:
            x_fid = np.array([point[0] for point in fidIm])
            y_fid_im = np.array([point[1] for point in fidIm])
            p1.plot(x_fid, y_fid_im, pen=pg.mkPen(color=colors['fidIm'], width=1), name='FID Imaginary')

        if fidMod:
            x_fid = np.array([point[0] for point in fidMod])
            y_fid_mod = np.array([point[1] for point in fidMod])
            p1.plot(x_fid, y_fid_mod, pen=pg.mkPen(color=colors['fidMod'], width=1), name='FID Magnitude')

        if lorenz:
            x_lorenz = np.array([point[0] for point in lorenz])
            y_lorenz = np.array([point[1] for point in lorenz])
            p1.plot(x_lorenz, y_lorenz, pen=pg.mkPen(color=colors['lorenz'], width=1), name='Lorenz Fitting Curve')

        # Plot FFT data
        if fftRe:
            x_fft = np.array([point[0] for point in fftRe])
            y_fft_re = np.array([point[1] for point in fftRe])
            p2.plot(x_fft, y_fft_re, pen=pg.mkPen(color=colors['fftRe'], width=1), name='FFT Real')

        if fftIm:
            x_fft = np.array([point[0] for point in fftIm])
            y_fft_im = np.array([point[1] for point in fftIm])
            p2.plot(x_fft, y_fft_im, pen=pg.mkPen(color=colors['fftIm'], width=1), name='FFT Imaginary')

        if fftMod:
            x_fft = np.array([point[0] for point in fftMod])
            y_fft_mod = np.array([point[1] for point in fftMod])
            p2.plot(x_fft, y_fft_mod, pen=pg.mkPen(color=colors['fftMod'], width=1), name='FFT Magnitude')

        if fftFit:
            x_fft = np.array([point[0] for point in fftFit])
            y_fft_fit = np.array([point[1] for point in fftFit])
            p2.plot(x_fft, y_fft_fit, pen=pg.mkPen(color=colors['fftFit'], width=1), name='FFT Fitting Curve')

    # Connect dropdown signal to update function
    step_selector.currentIndexChanged.connect(update_plot)

    # If there is data, initialize chart
    if graph_data:
        update_plot(0)

    # Show main window
    main_window.show()

    logger.info("Chart data plotting completed")
    app.exec_()

def read_spinq_file(file_path: str):
    pulse_data = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

            # 解析文件
            for line in lines:
                line = line.strip()

                # 解析脉冲数据（逗号分隔的数据行）
                if ',' in line and not line.startswith('##'):
                    values = line.split(',')
                    data_point = [float(val.strip()) for val in values]
                    pulse_data.append(data_point)

                # 文件结束标记
                elif line.startswith('##END='):
                    break

    except FileNotFoundError:
        logger.error(f"could not find pulse file: {file_path}")
    except Exception as e:
        logger.error(f"error: {str(e)}")
    return pulse_data

def parse_spinq_file(file_path: str):
    pulse_data = read_spinq_file(file_path)
    pulses = []
    for pulse in pulse_data:
        pulses.append(Pulse(
            path=0,
            amplitude=pulse[0],
            phase=pulse[1],
            width=pulse[2],
            detuning=0
        ))
    return pulses

def pulse_domain_analysis(pulses: List[Pulse]):
    _require_plotting()
    """
    Analyze the domain characteristics of pulse sequences, calculating Fourier transform from time domain to frequency domain

    Args:
        pulses: List of pulse sequences

    Returns:
        Dictionary containing frequency domain analysis results, including frequency, real part, imaginary part and magnitude
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

    # Calculate total time interval
    total_duration = sum(durations)
    t_total = []
    pulse_signals = []
    pulse_signals_norm = []

    # Generate time domain signal for each pulse
    for i, pulse in enumerate(pulses):
        t_init = sum(durations[:i])
        t_end = t_init + durations[i]
        dt = (t_end - t_init) / sample_points

        for j in range(sample_points):
            t = t_init + j * dt
            t_total.append(t)

            # Generate complex pulse signal
            if amps[i] == 0:
                pulse_signals.append(complex(0, 0))
                pulse_signals_norm.append(complex(0, 0))
            else:
                # Calculate phase (convert degrees to radians)
                phase_rad = phases[i] / 360.0 * 2 * math.pi
                # Calculate frequency (considering detuning)
                freq = detunings[i]

                # Generate complex signal
                real_part = amps[i] * math.cos(2 * math.pi * freq * t + phase_rad)
                imag_part = amps[i] * math.sin(2 * math.pi * freq * t + phase_rad)

                pulse_signals.append(complex(real_part, imag_part))
                pulse_signals_norm.append(complex(real_part / max_amp, imag_part / max_amp))

    # Pad signal length to power of 2 to improve FFT efficiency
    length = 2 ** math.ceil(math.log2(len(pulse_signals) * 5))

    # If no valid data, return empty result
    if length == 0:
        return {
            "freqs": [],
            "real": [],
            "imag": [],
            "mod": []
        }

    # Zero-pad to specified length
    pulse_signals = np.pad(pulse_signals, (0, length - len(pulse_signals)), 'constant')
    pulse_signals_norm = np.pad(pulse_signals_norm, (0, length - len(pulse_signals_norm)), 'constant')

    # Perform FFT
    fft_result = fft(pulse_signals)
    fft_result_norm = fft(pulse_signals_norm)

    # Calculate frequency axis
    fs = sample_points / t_total[-1] if t_total else 1.0
    f = np.array([(i - length/2) * fs / length for i in range(length)])

    # Shift zero frequency component to center
    fft_result = fftshift(fft_result)
    fft_result_norm = fftshift(fft_result_norm)

    # Define frequency range of interest
    freq_range = int(length * 0.1)  # Take 10% range around center

    start_idx = length // 2 - freq_range
    end_idx = length // 2 + freq_range

    # Extract data in specified range
    freqs = f[start_idx:end_idx].tolist()
    fft_selected = fft_result[start_idx:end_idx]
    fft_norm_selected = fft_result_norm[start_idx:end_idx]

    # Calculate magnitude
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

    # Create chart area
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


def decompress_graph_result(compressed_base64: str, original_size: int = 0, compressed_size: int = 0) -> List[Dict[str, Any]]:
    """
    Decompress graph result data

    Args:
        compressed_base64: Base64 encoded compressed data
        original_size: Original data size (bytes)
        compressed_size: Compressed data size (bytes)

    Returns:
        Decompressed graph result data list, format:
        [
            {
                "fidRe": {"x": [1.0, 1.1, ...], "y": [2.0, 2.1, ...]},
                "fidIm": {"x": [...], "y": [...]},
                "fftRe": {"x": [...], "y": [...]},
                "fftIm": {"x": [...], "y": [...]},
                "fftFit": {"x": [...], "y": [...]}
            }
        ]

    Raises:
        Exception: Thrown when decompression fails
    """
    # Validate input parameters
    if not compressed_base64:
        raise ValueError("Compressed data is empty, cannot decompress")

    if not isinstance(compressed_base64, str):
        raise TypeError(f"Compressed data must be string type, current type: {type(compressed_base64)}")

    try:
        # Base64 decode
        compressed_data = base64.b64decode(compressed_base64)

        # Validate decoded data
        if not compressed_data:
            raise ValueError("Data is empty after Base64 decoding")

        # Qt's qCompress uses zlib compression, but the first 4 bytes are the size of uncompressed data (big-endian)
        # Need to skip these 4 bytes
        if len(compressed_data) <= 4:
            raise ValueError(f"Compressed data length insufficient, needs at least 5 bytes, actual length: {len(compressed_data)}")
        # Use zlib decompression (skip the 4-byte header added by Qt)
        try:
            decompressed_data = zlib.decompress(compressed_data[4:])
        except zlib.error as e:
            raise ValueError(f"zlib decompression failed: {str(e)}")

        if not decompressed_data:
            raise ValueError("Decompressed data is empty")
        # Parse JSON data
        try:
            graph_result = json.loads(decompressed_data.decode('utf-8'))
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON parsing failed: {str(e)}")
        except UnicodeDecodeError as e:
            raise ValueError(f"UTF-8 decoding failed: {str(e)}")

        # Validate return data format
        if not isinstance(graph_result, list):
            raise TypeError(f"Decompressed data must be list type, current type: {type(graph_result)}")

        return graph_result

    except (ValueError, TypeError) as e:
        raise Exception(f"Failed to decompress graph data: {str(e)}")
    except Exception as e:
        raise Exception(f"Unknown error occurred while decompressing graph data: {str(e)}")

def convert_graph_to_graph(graph_result: List[Dict[str, Any]]) -> List[Dict[str, List[List[float]]]]:
    """
    Convert graph result data to graph format for visualization.

    Args:
        graph_result: The graph result data, in the format:
            [
                {
                    "fidRe": {"x": [1.0, 1.1, ...], "y": [2.0, 2.1, ...]},
                    "fidIm": {"x": [...], "y": [...]},
                    ...
                }
            ]

    Returns:
        The converted graph format data, in the format:
        [
            {
                "fidRe": [[x1, y1], [x2, y2], ...],
                "fidIm": [[x1, y1], [x2, y2], ...],
                ...
            }
        ]
    """
    # Validate input parameters
    if graph_result is None:
        return []
    if not isinstance(graph_result, list):
        return []
    if len(graph_result) == 0:
        return []
    graph = []

    for step_idx, step_data in enumerate(graph_result):
        # Validate step_data format
        if not isinstance(step_data, dict):
            continue

        if not step_data:
            continue

        graph_step = {}

        for key in ['fidRe', 'fidIm', 'fidMod', 'lorenz', 'fftRe', 'fftIm', 'fftMod', 'fftFit']:
            if key in step_data:
                data = step_data[key]

                # Skip None values
                if data is None:
                    continue

                # Check if x and y data exist
                if isinstance(data, dict) and 'x' in data and 'y' in data:
                    x_data = data['x']
                    y_data = data['y']

                    # Validate x and y data
                    if x_data is None or y_data is None:
                        continue

                    if not isinstance(x_data, list) or not isinstance(y_data, list):
                        continue

                    if len(x_data) == 0 or len(y_data) == 0:
                        continue

                    if len(x_data) != len(y_data):
                        min_len = min(len(x_data), len(y_data))
                        x_data = x_data[:min_len]
                        y_data = y_data[:min_len]

                    wave_data = []
                    for i in range(len(x_data)):
                        try:
                            x_val = x_data[i]
                            y_val = y_data[i]

                            # Skip None values
                            if x_val is None or y_val is None:
                                continue

                            # Try to convert to float
                            try:
                                x_float = float(x_val)
                                y_float = float(y_val)
                                wave_data.append([x_float, y_float])
                            except (ValueError, TypeError) as e:
                                continue
                        except IndexError:
                            break
                        except Exception as e:
                            continue

                    # Only add to graph_step when wave_data is not empty
                    if wave_data:
                        graph_step[key] = wave_data

        # Complete fidMod
        if 'fidMod' not in graph_step and 'fidRe' in graph_step and 'fidIm' in graph_step:
            try:
                fidRe = graph_step['fidRe']
                fidIm = graph_step['fidIm']
                if len(fidRe) == len(fidIm) and len(fidRe) > 0:
                    fidMod = []
                    for i in range(len(fidRe)):
                        try:
                            if len(fidRe[i]) >= 2 and len(fidIm[i]) >= 2:
                                x_val = float(fidRe[i][0])
                                re_val = float(fidRe[i][1])
                                im_val = float(fidIm[i][1])
                                mod_val = (re_val**2 + im_val**2)**0.5
                                fidMod.append([x_val, mod_val])
                        except (ValueError, TypeError, IndexError) as e:
                            continue
                    if fidMod:
                        graph_step['fidMod'] = fidMod
            except Exception as e:
                raise Exception(f"Unknown error occurred while completing fidMod for step {step_idx}: {str(e)}")

        # Complete fftMod
        if 'fftMod' not in graph_step and 'fftRe' in graph_step and 'fftIm' in graph_step:
            try:
                fftRe = graph_step['fftRe']
                fftIm = graph_step['fftIm']
                if len(fftRe) == len(fftIm) and len(fftRe) > 0:
                    fftMod = []
                    for i in range(len(fftRe)):
                        try:
                            if len(fftRe[i]) >= 2 and len(fftIm[i]) >= 2:
                                x_val = float(fftRe[i][0])
                                re_val = float(fftRe[i][1])
                                im_val = float(fftIm[i][1])
                                mod_val = (re_val**2 + im_val**2)**0.5
                                fftMod.append([x_val, mod_val])
                        except (ValueError, TypeError, IndexError) as e:
                            continue
                    if fftMod:
                        graph_step['fftMod'] = fftMod
            except Exception as e:
                raise Exception(f"Unknown error occurred while completing fftMod for step {step_idx}: {str(e)}")

        # Only add to graph when graph_step is not empty
        if graph_step:
            graph.append(graph_step)
        else:
            continue

    return graph

def process_experiment_graph(graph_result_compressed: str) -> Dict[str, Any]:
    """
    Process experiment result data, including decompression and conversion
    graph_result_compressed: Base64 encoded compressed graph data
    """
    graph_result = decompress_graph_result(graph_result_compressed)
    graph = convert_graph_to_graph(graph_result)
    return graph


class WaveformGenerator(WaveformGeneratorBase):
    """SpinQLink-compatible facade over the shared waveform algorithm."""

    pulse_type = Pulse
