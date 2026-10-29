Rabi pulse-width scan
==========================================

This is a full measured scan. Adjust pulse widths and scan ranges to the actual calibration. Raw measured points are retained; fit quality is reported separately from task completion.

The current ``fit_rabi`` helper needs at least five finite measurements and
searches periods from 40 to 800 microseconds. Fit quality is GOOD for
R-squared >= 0.8, ESTIMATE for >= 0.6 and POOR otherwise. The scan's final
assessment also flags estimates at the search boundary for inspection.
These are software fitting limits; calibrations outside them require a suitable
analysis rather than accepting the returned estimate as a device measurement.

.. literalinclude:: ../../../../../examples/lab/two/principles/rabi_scan.py
   :language: python
