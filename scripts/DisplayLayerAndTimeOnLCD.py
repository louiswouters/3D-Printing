# Cura PostProcessingPlugin
# Author:   Gwylan Scheeren
# Date:     31 May 2020
# Adapted from 'DisplayRemainingTimeOnLCD' by Mathias Lyngklip Kjeldgaard and 'DisplayFilenameAndLayerOnLCD' by Amanda de Castilho

# Description:  This plugin shows the current printing layer on your printers' LCD
#               Additionally it can shows the total layers and the remaining printing   time.
#               - Display total layers: This setting shows the total number of layers to print next to the current layer. ENABLED BY DEFAULT
#               - Display ETA: This setting shows the remaining printing time. ENABLED BY DEFAULT

from ..Script import Script
from UM.Application import Application

import re
import datetime

class DisplayLayerAndTimeOnLCD(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "Display Layer And ETA On LCD",
            "key": "DisplayLayerAndTimeOnLCD",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "maxlayer":
                {
                    "label": "Display total layers?:",
                    "description": "This setting shows the total number of layers to print, next to the current layer.",
                    "type": "bool",
                    "default_value": true
                },
                "timeETA":
                {
                    "label": "Display ETA",
                    "description": "This setting shows the remaining printing time.",
                    "type": "bool",
                    "default_value": true
                }
            }
        }"""

    def execute(self, data):
        total_time = 0 # initialize variables and counter
        total_time_string = ""
        max_layer = 0
        lcd_text = "M117 Layer "
        i = 1
        for layer in data:
            display_text = lcd_text + str(i) # create base LCD message with updated current layer
            layer_index = data.index(layer) # get current layer index
            lines = layer.split("\n")
            for line in lines:
                if self.getSettingValueByKey("timeETA"):
                    if line.startswith(";TIME:"):
                        # At this point, we have found a line in the GCODE with ";TIME:"
                        # which is the indication of total_time. Looks like: ";TIME:1337", where
                        # 1337 is the total print time in seconds.
                        line_index = lines.index(line)          # We take a hold of that line
                        split_string = re.split(":", line)      # Then we split it, so we can get the number

                        string_with_numbers = "{}".format(split_string[1])      # Here we insert that number from the
                                                                                # list into a string.
                        total_time = int(string_with_numbers) + 1                  # Only to contert it to a int. And add 1 second so as to prevent negative total time at the end.

                        m, s = divmod(total_time, 60)    # Math to calculate
                        h, m = divmod(m, 60)             # hours, minutes and seconds.
                        total_time_string = "{:d}h{:02d}m{:02d}s".format(h, m, s)           # Now we put it into the string
                        lines.insert(line_index + 1, "M117 Print duration {}".format(total_time_string))   # And print that string instead of the original one

                if line.startswith(";LAYER_COUNT:"):
                    max_layer = line # get line
                    max_layer = max_layer.split(":")[1] # split to extract total number of layers

                if line.startswith(";LAYER:"):
                    if self.getSettingValueByKey("maxlayer"):
                        display_text = display_text + " of " + max_layer # if enabled add total number of layers to LCD message
                    i += 1 # update current layer counter

                if line.startswith(";TIME_ELAPSED:"):

                    # As we didnt find the total time (";TIME:"), we have found a elapsed time mark
                    # This time represents the time the printer have printed. So with some math;
                    # totalTime - printTime = RemainingTime.
                    line_index = lines.index(line)          # We get a hold of the line
                    nextline = lines[line_index + 1]
                    list_split = re.split(":", line)        # Again, we split at ":" so we can get the number
                    string_with_numbers = "{}".format(list_split[1])   # Then we put that number from the list, into a string

                    current_time = float(string_with_numbers)       # This time we convert to a float, as the line looks something like:
                                                                    # ;TIME_ELAPSED:1234.6789
                                                                    # which is total time in seconds

                    time_left = total_time - current_time   # Here we calculate remaining time
                    m1, s1 = divmod(time_left, 60)          # And some math to get the total time in seconds into
                    h1, m1 = divmod(m1, 60)                 # the right format. (HH,MM,SS)
                    current_time_string = "{:d}h{:2d}m{:2d}s".format(int(h1), int(m1), int(s1))   # Here we create the string holding our time

                    if (int(i) == int(max_layer) + 1):
                        display_text = "M117 Printed {} layers in {}".format(max_layer, total_time_string) # if last timestamp is detected the ending message will report total number of layers and printing time
                    elif self.getSettingValueByKey("timeETA"):
                        display_text = display_text + " | ETA {}".format(current_time_string) # if enabled add remaining printing time to LCD message
                    lines.insert(line_index + 1, display_text) # insert LCD message in array

            final_lines = "\n".join(lines) # join lines for this section of GCODE file
            data[layer_index] = final_lines

        return data