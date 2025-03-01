# This file contains boilerplate code to allow users write their model
# inference code that will then interact with the Triton Inference Server
# Python backend to serve end user requests.
# The module name, module path, class name & get_predictions() method names MUST be maintained as is
# but other methods may be added within the class as deemed fit provided
# they are invoked within the main get_predictions() inference method
# if they play a role in any step of model inference
"""User model inference script."""

import os
from pathlib import Path
import numpy as np
from clarifai.models.model_serving.model_config import ModelTypes, get_model_config

config = get_model_config(ModelTypes.visual_embedder)


class InferenceModel:
  """User model inference class."""

  def __init__(self) -> None:
    """
    Load inference time artifacts that are called frequently .e.g. models, tokenizers, etc.
    in this method so they are loaded only once for faster inference.
    """
    self.base_path: Path = os.path.dirname(__file__)
    ## sample model loading code:
    #self.checkpoint_path: Path = os.path.join(self.base_path, "your checkpoint filename/path")
    #self.model: Callable = <load_your_model_here from checkpoint or folder>

  #Add relevant model type decorator to the method below (see docs/model_types for ref.)
  @config.inference.wrap_func
  def get_predictions(self, input_data, **kwargs):
    """
    Main model inference method.

    Args:
    -----
      input_data: A single input data item to predict on.
        Input data can be an image or text, etc depending on the model type.

    Returns:
    --------
      One of the clarifai.models.model_serving.models.output types. Refer to the README/docs
    """
    outputs = []

    for inp in input_data:
      assert isinstance(inp, np.ndarray), "Incorrect type of image, expected np.ndarray"
      output = np.random.randn(768)
      output = config.inference.return_type(output)
      outputs.append(output)

    return outputs
