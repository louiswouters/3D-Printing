# Cura PostProcessingPlugin
# Author:   Louis Wouters
# Date:     06-06-2020

# Description:  This plugin will turn of the heated bed after a certain amount of layers or time has passed.

from ..Script import Script


class TurnOffHeatedBedAfterLayer(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "Turn off heated bed after layer",
            "key": "TurnOffHeatedBedAfterLayer",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "turn_off_after_layer":
                {
                    "label": "Turn off after layer",
                    "description": "After this many layers, the heated bed will be turned off.",
                    "type": "int",
                    "default_value": 3
                },
                "minimum_minutes_after_first_layer":
                {
                    "label": "Minimum time after first layer",
                    "description": "The bed won't be turned off if the minimum time hasn't passed",
                    "type": "int",
                    "unit": "minutes",
                    "default_value": 0
                }
            }
        }"""

    def execute(self, data):
        # get settings
        turn_off_after_layer = self.getSettingValueByKey("turn_off_after_layer")
        minimum_minutes_after_first_layer = self.getSettingValueByKey("minimum_minutes_after_first_layer")

        # initialize global variables
        first_layer_index = 0
        time_total = 0
        number_of_layers = 0
        first_layer_duration_seconds = 0
        minutes_after_first_layer = 0
        minimum_layer = 0

        # Search for the number of layers and the total time from the start code
        for index in range(len(data)):
            data_section = data[index]
            if data_section.startswith(";LAYER:"):  #  we have everything we need, save the index of the first layer and exit the loop
                first_layer_index = index
                break
            else:
                for line in data_section.split("\n"):  # Seperate into lines
                    if line.startswith(";LAYER_COUNT:"):
                        number_of_layers = int(line.split(":")[1])  # Save total layers in a variable
                    elif line.startswith(";TIME:"):
                        time_total = int(line.split(":")[1])  # Save total time in a variable

        if number_of_layers <= turn_off_after_layer or time_total / 60 < minimum_minutes_after_first_layer:
            return data  # No adjustment needed, the end G-code will turn the bed off

        #  determine after which layer enough time has passed
        for layer_counter in range(number_of_layers):
            if layer_counter + 1 == number_of_layers:
                return data  # No adjustment needed, the end G-code will turn the bed off

            #  create a list where each element is a single line of code within the layer
            lines = data[first_layer_index + layer_counter].split("\n")

            # search for TIME_ELAPSED at the end of the layer
            for line_index in range(len(lines) - 1, -1, -1):
                line = lines[line_index]  # store the line as a string
                if line.startswith(";TIME_ELAPSED:"):
                    time_elapsed = float(line.split(":")[1])
                    if layer_counter == 0:
                        first_layer_duration_seconds = time_elapsed
                    else:
                        minutes_after_first_layer = (time_elapsed - first_layer_duration_seconds) / 60
                    break

            if minutes_after_first_layer >= minimum_minutes_after_first_layer:
                minimum_layer = layer_counter + 1
                break

        #  add the code to turn of the bed at the end of the right layer.
        turn_off_after_layer = max(minimum_layer, turn_off_after_layer)
        data[first_layer_index+turn_off_after_layer-1] += "M140 S0 ; Turn of heated bed\n"

        return data
