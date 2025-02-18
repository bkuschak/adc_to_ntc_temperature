# Generate a lookup table to convert ratiometric ADC values directly to
# temperature. For use with NTC thermistor voltage divider, where ADC VREF
# is applied across the voltage divider. The NTC thermistor may be located
# on either the top side or bottom side of the divider.
#
# The table is constructed in one of two ways:
# - Using a beta value, reference temperature, and reference resistance.
# - Using 3 or 4 Steinhart-Hart coefficients.
#
# Using the Beta value, the resulting table is accurate over some range of
# temperatures, but becomes less accurate as the range increases. Using
# Steinhart-Hart coefficients, the table may be more accurate over a larger
# temperature range.
#
# The resulting code is fast, using one integer multiply and some additions and
# bit shifts.
#
# Adapted from https://www.sebulli.com/ntc/index.php

import argparse
import math
import numpy as np
import os
import sys

class ntc_lookup_table:

    # Reference resistance is the thermistor resistance at the reference
    # temperature. Other resistance is the other resistor in the voltage
    # divider.
    def __init__(self, adc_bits, table_bits, temperature_resolution, beta,
                 reference_resistance, reference_temperature, other_resistance,
                 steinhart_coefficients=None, thermistor_on_top=False):
        if beta and beta <= 0:
            raise ValueError("beta must be > 0")
        if reference_resistance and reference_resistance <= 0:
            raise ValueError("reference resistance must be > 0")
        if other_resistance <= 0:
            raise ValueError("other_resistance must be > 0")
        if temperature_resolution <= 0:
            raise ValueError("temperature_resolution must be > 0")
        if adc_bits < table_bits:
            raise ValueError("table_bits must be <= adc_bits")
        if steinhart_coefficients and len(steinhart_coefficients) != 4:
            raise ValueError("must provide 4 Steinhart-Hart coefficients")

        self.adc_bits = adc_bits
        self.table_bits = table_bits
        self.temperature_resolution = temperature_resolution
        self.beta = beta
        self.reference_resistance = reference_resistance
        self.reference_temperature = reference_temperature
        self.other_resistance = other_resistance
        self.thermistor_on_top = thermistor_on_top
        self.table = None
        self.steinhart_coefficients = steinhart_coefficients

    # Given an integer ADC value, scale it to a range between 0 and 1.
    def normalized_adc_value(self, adc_value, num_bits):
        return float(adc_value) / 2^num_bits;

    # Given a divider ratio and the high-side resistance value, return the
    # low-side resistance value.
    def low_side_resistance(self, divider_ratio, high_side_resistance):
        if divider_ratio < 0 or divider_ratio >= 1:
            raise ValueError("divider_ratio out of range (0 to 1)")
        if high_side_resistance < 0:
            raise ValueError("high_side_resistance must be >= 0")
        return high_side_resistance * divider_ratio / (1 - divider_ratio)

    # Given a divider ratio and the low-side resistance value, return the
    # high-side resistance value.
    def high_side_resistance(self, divider_ratio, low_side_resistance):
        if divider_ratio <= 0 or divider_ratio > 1:
            raise ValueError("divider_ratio out of range (0 to 1)")
        if low_side_resistance < 0:
            raise ValueError("low_side_resistance must be >= 0")
        return low_side_resistance * (1 - divider_ratio) / divider_ratio

    # Generalized formula for NTC resistance, using the thermistor 'beta'
    # value:
    # T = β / ln(R / (R0 * exp(-β/T0)))
    # T0 = reference temperature (Kelvin)
    # R0 = resistance at reference temperature
    # R  = measured resistance
    # β  = thermal 'constant' near T0
    def resistance_to_temperature_beta(self, resistance):
        if resistance <= 0:
            raise ValueError("resistance must be > 0")
        Rinf = self.reference_resistance * math.exp(-self.beta /
                                                    (self.reference_temperature
                                                     + 273.15))
        temp = float(self.beta) / math.log(resistance / Rinf)
        return temp - 273.15

    # The four-parameter version of the S.H. equation. Returns temperature as
    # a function of resistance. For the three-parameter version of the S.H.
    # equation, a2 should equal zero.
    def resistance_to_temperature_steinhart(self, resistance):
        if resistance <= 0:
            raise ValueError("resistance must be > 0")
        if len(self.steinhart_coefficients) != 4:
            raise ValueError("invalid Steinhart-Hart coefficients")
        a0, a1, a2, a3 = self.steinhart_coefficients
        r = resistance
        temperature = 1.0 / (a0 + a1*np.log(r) + a2*(np.log(r)**2) +
                      a3*(np.log(r)**3))
        return temperature - 273.15

    # Calculate the thermistor resistance, then temperature.
    def calc_temp_c(self, divider_ratio):
        if self.thermistor_on_top:
            thermistor_r = self.high_side_resistance(divider_ratio,
                                                     self.other_resistance)
        else:
            thermistor_r = self.low_side_resistance(divider_ratio,
                                                    self.other_resistance)

        # Given the resistance, calculate the temperature using either
        # the beta equation or Steinhart-Hart.
        if self.steinhart_coefficients != None:
            temp_c = self.resistance_to_temperature_steinhart(thermistor_r)
        else:
            temp_c = self.resistance_to_temperature_beta(thermistor_r)
        temp_c /= self.temperature_resolution
        temp_c = int(temp_c)
        return temp_c

    # Table size will be (2^num_bits) + 1, usually a subset of the ADC range.
    # The MSBs of the ADC value are used as an index into the table.
    # Temperature resolution is typically 0.1 or 0.01, or 0.001, and affects
    # the size of the integers in the table.

    def generate_table(self):
        self.table_len = 2**self.table_bits + 1
        self.table = [None] * self.table_len

        # Calculate the table, excluding the first and last entries.
        for i in range(1, self.table_len-1):
            # ADC is ratiometric, so the ADC value is fixed point 0 to 1, and
            # is equal to the resistor divider ratio.
            divider_ratio = normalized_adc = float(i) / 2**self.table_bits
            self.table[i] = self.calc_temp_c(divider_ratio)

        # The first and last entries will not be valid since they correspond to
        # a divider ratio of 0 and infinity, clearly not valid temperatures.
        # Let's recalculate the first and last entries, using a single
        # (full-resolution) LSB offset. This isn't ideal, but it will provide
        # something useable for interpolating at the extreme ends of the range.

        divider_ratio = normalized_adc = 1 / 2**self.adc_bits
        self.table[0] = self.calc_temp_c(divider_ratio)

        divider_ratio = normalized_adc = (2**self.adc_bits-1) / \
                                         2**self.adc_bits
        self.table[self.table_len-1] = self.calc_temp_c(divider_ratio)
        return self.table

    def int_type(self, val_min, val_max):
        if(val_min >= -2**7 and val_max < 2**7):
            int_type = 'int8_t'
        elif(val_min >= -2**15 and val_max < 2**15):
            int_type = 'int16_t'
        elif(val_min >= -2**31 and val_max < 2**31):
            int_type = 'int32_t'
        elif(val_min >= -2**63 and val_max < 2**63):
            int_type = 'int64_t'
        else:
            raise ValueError("Value(s) out of range.")
        return int_type

    def uint_type(self, val_max):
        if(val_max < 2**8):
            uint_type = 'uint8_t'
        elif(val_max < 2**16):
            uint_type = 'uint16_t'
        elif(val_max < 2**32):
            uint_type = 'uint32_t'
        elif(val_max < 2**64):
            uint_type = 'uint64_t'
        else:
            raise ValueError("Value out of range.")
        return uint_type

    # Generate a table for inclusion in C code.
    def generate_c_code(self):
        if self.table == None:
            raise ValueError("Table must be generated first!");

        # Determine the integer sizes.
        ttype = self.int_type(min(self.table), max(self.table))
        adc_type = self.uint_type(2**self.adc_bits-1)

        # Strings.
        side = 'top' if self.thermistor_on_top else 'bottom'
        if self.beta:
            coef_str = '{} ohms @ {} deg C. Beta: {}.'.format(
                    int(self.reference_resistance),
                    int(self.reference_temperature), int(self.beta))
        else:
            coef_str = 'Steinhart-Hart coefficients a0, a1, a2, a3:\n' \
                       ' *   {}, {}, {}, {}'.format(
                    self.steinhart_coefficients[0],
                    self.steinhart_coefficients[1],
                    self.steinhart_coefficients[2],
                    self.steinhart_coefficients[3])
        command_line = ' '.join(sys.argv)
        str = \
"""
#include <stdint.h>

/* ADC to temperature lookup table.
 * github.com/bkuschak/adc_to_ntc_temperature
 * Adapted from https://www.sebulli.com/ntc/index.php
 *
 * Command:
 * {}
 *
 * {}
 * NTC thermistor location: {} side of the voltage divider.
 * {} ohm resistor on opposite side of the voltage divider.
 * Input: {} MSBs of the ADC value.
 * Output: Temperature in units of {} deg C.
 * LSBs of ADC value should be used to interpolate between the nearest points.
 */
""".format(command_line, coef_str, side, int(self.other_resistance), self.table_bits,
           self.temperature_resolution)

        str += 'const {} ntc_table[{}] = {{\n'.format(ttype, len(self.table))
        i = 0
        line = '    '
        while i < len(self.table):
            val = "{}".format(self.table[i])
            if i != len(self.table)-1:
                val += ", "

            if len(line) + len(val) < 80:
                line += val;
            else:
                str += line + '\n'
                line = '    ' + val
            i += 1

        str += line
        str += '\n};'

        # Add the code to perform the interpolation.
        adc_mask = '{:X}'.format(2**self.adc_bits - 1)
        shift = self.adc_bits - self.table_bits
        mask = '{:X}'.format(2**shift - 1)

        if self.thermistor_on_top:
            interp = "return p1 + (((p2-p1) * (adc_value & 0x{}))>>{});". \
                     format(mask, shift)
        else:
            interp = "return p1 - (((p1-p2) * (adc_value & 0x{}))>>{});". \
                     format(mask, shift)

        str += '\n'
        str += \
"""
/*
 * Convert an ADC value into a temperature value.
 * The ADC value must be a ratiometric measurement of the NTC voltage divider.
 *
 * p1 and p2 are the interpolating points just before and after the ADC value.
 * The function interpolates between these two points. The resulting code is
 * very small and fast. Only one integer multiplication is used.
 *
 * adc_value: the ADC measurement, {} bits full scale, right justified.
 * Returns the temperature in units of {} °C
 *
 */
{} adc_to_temperature({} adc_value)
{{
  adc_value &= 0x{};

  /* Estimate the interpolating point before and after the ADC value. */
  {} p1 = ntc_table[ (adc_value >> {})  ];
  {} p2 = ntc_table[ (adc_value >> {})+1];

  /* Interpolate between both points. */
  {}
}}
""".format(self.adc_bits, self.temperature_resolution, ttype, adc_type,
           adc_mask, ttype, shift, ttype, shift, interp)

        return str

if __name__ == "__main__":
    os.environ['COLUMNS'] = '80'  # for printing --help
    description = \
"""
Generate a lookup table to convert ratiometric ADC values directly to
temperature. For use with NTC thermistor voltage divider, where ADC VREF
is applied across the voltage divider. The NTC thermistor may be located
on either the top side or bottom side of the divider.

The table is constructed in one of two ways:
1) Using a beta value, reference temperature, and reference resistance.
2) Using 3 or 4 Steinhart-Hart coefficients.

Using the Beta value, the resulting table is accurate over some range of
temperatures, but becomes less accurate as the range increases. Using
Steinhart-Hart coefficients, the table may be more accurate over a larger
temperature range.

The resulting code is fast, using one integer multiply and some additions and
bit shifts.

Adapted from https://www.sebulli.com/ntc/index.php
"""
    ap = argparse.ArgumentParser(epilog=description)
    ap.add_argument('--adc_bits', help='Number of bits of ADC resolution.',
                    type=int, required=True, dest='adc_bits')
    ap.add_argument('--table_bits', help='Number of bits. Table len = '
                    '2^TABLE_BITS + 1.', type=int, required=True,
                    dest='table_bits')
    ap.add_argument('--resolution', help='Temperature resolution (C). '
                    'Typically 0.01.', type=float, required=True,
                    dest='resolution', metavar='DEGREES')
    ap.add_argument('-R', help='Thermistor reference resistance (ohms).',
                    type=float, required=False, metavar='OHMS',
                    dest='reference_resistance')
    ap.add_argument('-T', help='Thermistor reference temperature (C).',
                    type=float, required=False, metavar='DEGREES',
                    dest='reference_temperature')
    ap.add_argument('-r', help='Other resistor value (ohms).', type=float,
                    required=True, metavar='OHMS', dest='other_resistance')
    ap.add_argument('-o', '--output', help='Output file to write.',
                    dest='output', metavar='OUTPUT')
    ap.add_argument('--plot', help='Create plot.', dest='plot',
                    action='store_true')

    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument('-B', '--beta', help='Thermistor beta value.',
                       type=float, dest='beta')
    group.add_argument('-S', '--steinhart', help='4 Steinhart-Hart '
                       'coefficients a0, a1, a2, a3. If using only 3 '
                       'coefficients (A, B, C) set a0=A, a1=B, a2=0, a3=C.',
                       metavar=('a0', 'a1', 'a2', 'a3'), nargs=4, type=float,
                       dest='steinhart')

    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument('-t', '--top', help='Thermistor on top-side of voltage '
                       'divider.', action='store_true', dest='top')
    group.add_argument('-b', '--bottom', help='Thermistor on bottom-side of '
                       'voltage divider.', action='store_true', dest='bottom')

    opts = ap.parse_args()
    if opts.beta and (opts.reference_resistance is None or
                      opts.reference_temperature is None):
        ap.error('-R and -T must be provided when using beta.')

    ntc = ntc_lookup_table(opts.adc_bits, opts.table_bits, opts.resolution,
                           opts.beta, opts.reference_resistance,
                           opts.reference_temperature,
                           opts.other_resistance, opts.steinhart, opts.top)
    lookup_table = ntc.generate_table()
    c_code = ntc.generate_c_code()

    if opts.output:
        with open(opts.output, "w") as f:
            f.write(c_code)
    else:
        print(c_code)

    if opts.plot:
        import matplotlib.pyplot as plt
        import numpy as np

        # Plot the generated table. Indicate those temperatures that fall
        # outside the range of temperatures provided by the input data. These
        # will have reduced accuracy.
        fig, ax = plt.subplots(1)
        fig.suptitle('ADC to NTC temperature lookup table. Table len: {}.'
                     .format(len(lookup_table)))
        table = np.array(lookup_table) * opts.resolution
        ax.plot(table, 'b-', label='Lookup table')
        ax.set_xlabel('The {} MSBs of the ADC value'.format(opts.table_bits))
        ax.set_ylabel('Temperature (°C)')
        ax.set_xlim(0, 2**opts.table_bits-1)
        ax.set_ylim(-40, 125)
        major_ticks = np.linspace(0, 2**opts.table_bits, 9)
        ax.set_xticks(major_ticks)
        ax.grid()
        h, l = ax.get_legend_handles_labels()
        ax.legend(h[::-1], l[::-1])
        fig.tight_layout()
        plt.show()

    exit(0)
