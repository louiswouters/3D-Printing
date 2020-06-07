# Cura PostProcessingPlugin
# Author:   Louis Wouters
# Date:     06-06-2020

# Description:  This plugin will change the temperature of the heated bed and/or nozzle at specified timestamps/layers

from ..Script import Script


class ChangeTemperatureDuringPrint(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "Change temperature during print",
            "key": "ChangeTemperatureDuringPrint",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "bed_temperature":
                {
                    "label": "Bed",
                    "description": "0 turns the heat bed off, negative values will leave the temperature unchanged",
                    "type": "int",
                    "unit": "°C",
                    "default_value": -1
                },
                "nozzle_temperature":
                {
                    "label": "Nozzle",
                    "description": "0 turns the nozzle off, negative values will leave the temperature unchanged",
                    "type": "int",
                    "unit": "°C",
                    "default_value": -1
                },
                "change_temperature_after_layer":
                {
                    "label": "Change temperature after",
                    "description": "The temperatures will change after this many layers. If set to 0, the temperature will change X minutes after the first layer has been printed",
                    "type": "int",
                    "unit": "layers",
                    "default_value": 3
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

        # Search for the number of layers and the total time from the start code
        first_layer_index = 0
        time_total = 0
        number_of_layers = 0
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

        # Check if adjustments to the G-code are necessary
        change_temperature_after_layer = self.getSettingValueByKey("change_temperature_after_layer")
        minimum_minutes_after_first_layer = self.getSettingValueByKey("minimum_minutes_after_first_layer")
        if number_of_layers <= change_temperature_after_layer or time_total / 60 < minimum_minutes_after_first_layer:
            return data  # No adjustment needed, let the end G-code turn of the bed and the nozzle

        #  determine after which layer enough time has passed
        first_layer_duration_seconds = 0
        minutes_after_first_layer = 0
        minimum_layer = 0
        for layer_counter in range(number_of_layers):
            if layer_counter + 1 == number_of_layers:
                return data  # No adjustment needed, let the end G-code turn of the bed and the nozzle

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

        #  construct the G-code that needs to be inserted
        insert_gcode = ""
        bed_temperature = self.getSettingValueByKey("bed_temperature")
        nozzle_temperature = self.getSettingValueByKey("nozzle_temperature")
        if bed_temperature > 0:
            insert_gcode += "M140 S"+str(bed_temperature)+" ; Set bed to "+str(bed_temperature)+"°C\n"
        elif bed_temperature == 0:
            insert_gcode += "M140 S0 ; Turn off bed\n"
        if nozzle_temperature > 0:
            insert_gcode += "M104 S"+str(nozzle_temperature)+" ; Set nozzle to "+str(nozzle_temperature)+"°C\n"
        elif nozzle_temperature == 0:
            insert_gcode += "M104 S0 ; Turn off nozzle\n"

        #  add the constructed G-dode at the end of the layer
        turn_off_after_layer = max(minimum_layer, change_temperature_after_layer)
        layer_index = first_layer_index + turn_off_after_layer - 1  # index of the layer where the code is inserted
        data[layer_index] += insert_gcode

        return data
