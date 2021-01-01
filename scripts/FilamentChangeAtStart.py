# Cura PostProcessingPlugin
# Author:   Louis Wouters
# Date:     06-06-2020

from ..Script import Script


class FilamentChangeAtStart(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "Filament change at start",
            "key": "FilamentChangeAtStart",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "enabled":
                {
                    "label": "Enabled",
                    "description": "If checked, filament change will be done at the start of the print",
                    "type": "bool",
                    "default_value": true
                },
                "number_of_cleaning_lines":
                {
                    "label": "Number of cleaning lines",
                    "description": "The print head will print a line back and forth to clear out the previous color",
                    "type": "int",
                    "unit": "lines",
                    "default_value": 3
                }
            }
        }"""

    def execute(self, data):

        # if the feature is not enabled, return the original g-code file without modification
        if not self.getSettingValueByKey("enabled"):
            return data

        # Search for first layer
        first_layer_index = 0

        for index in range(len(data)):
            data_section = data[index]
            if data_section.startswith(";LAYER:"):
                first_layer_index = index           # ...save the index of the first layer
                break                               # ......and exit the loop

        number_of_cleaning_lines = self.getSettingValueByKey("number_of_cleaning_lines")
        insert_gcode = "G1 Z2.0 F3000 ; Move Z Axis up little to prevent scratching of Heat Bed\n"
        insert_gcode += "M0 ; wait for user input\nG28 ; home\n"
        insert_gcode += "M117 Cleaning nozzle\nG1 X0.1 Y20 Z0.3 F5000.0 ; Move to start position\nG91\n"
        insert_gcode += "G1 Y180 F1500 E15 ; Up\nG1 X0.3 F5000 ; Right\nG1 Y-180 F1500.0 E15 ; Down\nG1 X0.3 F5000 ; Right\n" * number_of_cleaning_lines
        insert_gcode += "G1 Z1.7 F3000 ; Move Z Axis up little to prevent scratching of Heat Bed\nG1 X5  Z-1.7 F5000 ; Move over to prevent blob squish\nG90\nG92 E0 ; Reset Extruder\n"

        #  add the constructed G-code at the end of the layer
        layer_index = first_layer_index - 1  # index of the layer where the code is inserted
        data[layer_index] += insert_gcode

        return data
