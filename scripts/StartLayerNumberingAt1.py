# Cura PostProcessingPlugin
# Author:   Louis Wouters
# Date:     06-06-2020

# Description:  This plugin will turn of the heated bed after a certain amount of layers or time has passed.

from ..Script import Script


class StartLayerNumberingAt1(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "Start layer numbering at 1",
            "key": "StartLayerNumberingAt1",
            "metadata": {},
            "version": 2,
            "settings":{}
        }"""

    def execute(self, data):

        # initialize global variables
        first_layer_index = 0
        number_of_layers = 0

        # Search for the number of layers from the start code
        for index in range(len(data)):
            data_section = data[index]
            if data_section.startswith(";LAYER:"):  # we have everything we need
                first_layer_index = index           # ...save the index of the first layer
                break                               # ......and exit the loop
            else:
                for line in data_section.split("\n"):  # Separate into lines
                    if line.startswith(";LAYER_COUNT:"):
                        number_of_layers = int(line.split(":")[1])  # Save total layers in a variable

        #  for each layer
        for layer_counter in range(number_of_layers):
            layer_index = first_layer_index + layer_counter
            layer = data[layer_index]  # get the current layer
            layer = layer[layer.find("\n"):]  # remove the first line
            layer = ";LAYER:" + str(layer_counter + 1) + layer  # insert the correct line in the layer
            data[layer_index] = layer  # overwrite the layer in the data

        return data
