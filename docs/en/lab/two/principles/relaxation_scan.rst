T1/T2 relaxation scans
============================================

This is a full measured scan. Adjust pulse widths and scan ranges to the actual calibration. Raw measured points are retained; fit quality is reported separately from task completion.

Install the ``plot`` extra for SciPy-based fitting. The current T1/T2 helpers
need at least three finite measurements. Input delays and fitted lifetimes use
microseconds: T1 is bounded to 10000..60000000 and T2 to 1000..20000000.
Fit quality is GOOD for R-squared >= 0.8, ESTIMATE for >= 0.6 and POOR otherwise.
Inspect fits against the actual scan and calibration; these bounds and quality
labels do not establish scientific success.

.. literalinclude:: ../../../../../examples/lab/two/principles/relaxation_scan.py
   :language: python
