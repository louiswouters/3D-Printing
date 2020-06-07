# Cura PostProcessingPlugin
# Author:   Louis Wouters
# Date:     06-06-2020

# Description:  This plugin will turn of the heated bed after a certain amount of layers or time has passed.

from ..Script import Script


class ChangeBedTemperatureAfterLayer(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "Change bed temperature after layer",
            "key": "ChangeBedTemperatureAfterLayer",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "change_temperature_after_layer":
                {
                    "label": "Change temperature after",
                    "description": "After this many layers, the bed temperature will change. If this is set to 0 or 1, the temperature will change X minutes after the first layer has been printed",
                    "type": "int",
                    "unit": "layers",
                    "default_value": 3
                },
                "temperature":
                {
                    "label": "Temperature",
                    "description": "Choose 0 to turn the heated bed off",
                    "type": "int",
                    "unit": "°C",
                    "default_value": 0
                },
                "minimum_minutes_after_first_layer":
                {
                    "label": "Minimum time after first layer",
                    "description": "Minimum time to wait after the first layer has been printed before changing the temperature. If set to 0, the temperature will change after X layers",
                    "type": "int",
                    "unit": "minutes",
                    "default_value": 0
                }
            }
        }"""

    def execute(self, data):
        # get settings
        change_temperature_after_layer = self.getSettingValueByKey("change_temperature_after_layer")
        temperature = self.getSettingValueByKey("temperature")
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
            if data_section.startswith(";LAYER:"):  # we have everything we need
                first_layer_index = index           # ...save the index of the first layer
                break                               # ......and exit the loop
            else:
                for line in data_section.split("\n"):  # Separate into lines
                    if line.startswith(";LAYER_COUNT:"):
                        number_of_layers = int(line.split(":")[1])  # Save total layers in a variable
                    elif line.startswith(";TIME:"):
                        time_total = int(line.split(":")[1])  # Save total time in a variable

        if number_of_layers <= change_temperature_after_layer or time_total / 60 < minimum_minutes_after_first_layer:
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

        #  add the code to change the bed temperature at the end of the right layer.
        turn_off_after_layer = max(minimum_layer, change_temperature_after_layer)
        layer_index = first_layer_index + turn_off_after_layer - 1  # index of where to insert the code
        data[layer_index] += "M140 S" + str(temperature) + " ; Set bed temperature to " + str(temperature) + "°C\n"

        return data
