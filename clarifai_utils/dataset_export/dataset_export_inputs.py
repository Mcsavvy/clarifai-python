import os
import tempfile
import zipfile
from io import BytesIO

import requests
from PIL import ImageFile
from proto.clarifai.api import resources_pb2
from tqdm import tqdm


class DatasetExportReader:
  """
  Unpacks the zipfile from DatasetVersionExport
  - Downloads the temp archive onto disk
  - Reads DataserVersionExports archive in memory without extracting all
  - Yield each api.Data object.
  """

  def __init__(self, archive_url=None, local_archive_path=None):

    self.file_name_list = None
    self.len_file_name_list = 0
    self.input_count = 0
    self.archive_url = archive_url
    self.local_archive_path = local_archive_path
    self.temp_file = None
    self.archive = None

    assert archive_url or local_archive_path, "Must use one input."

    if archive_url:
      print('url: %s' % self.archive_url)
      self._download_temp_archive()
    else:
      print("path: %s" % local_archive_path)
      self.archive = zipfile.ZipFile(local_archive_path)

    self._get_archive_name_list()

  def _download_temp_archive(self, chunk_size=128):
    """
    Downloads the temp archive of DataBatches.
    """
    r = requests.get(self.archive_url, stream=True)
    self.temp_file = tempfile.TemporaryFile()
    for chunk in r.iter_content(chunk_size=chunk_size):
      self.temp_file.write(chunk)

    self.archive = zipfile.ZipFile(self.temp_file)

  def _get_archive_name_list(self):
    """
    Extract the file name list, split directory (e.g. all, train etc).
    """
    file_name_list = self.archive.namelist()
    self.file_name_list = file_name_list
    self.len_file_name_list = len(file_name_list)
    print("Obtained file name list. %d entries." % self.len_file_name_list)

    self.split_dir = os.path.dirname(self.file_name_list[0]) if self.len_file_name_list else ""

  def __len__(self):
    if self.input_count:
      return self.input_count
    else:
      cnt = 0
      if self.file_name_list is not None:
        for filename in self.file_name_list:
          cnt += int(filename.split('_n')[-1])
        self.input_count = cnt
      return cnt

  def __iter__(self):
    """
    Loops through all DataBatches in the DatasetVersionExport and yields every api.Data object
    """
    if self.file_name_list is not None:
      for filename in self.file_name_list:
        db = resources_pb2.DataBatch().FromString(self.archive.read(filename))
        for data in db.data:
          yield data
      print("DONE")

  def __enter__(self):
    return self

  def __exit__(self, *args):
    self.close()

  def close(self):
    print("closing file objects.")
    self.archive.close()
    if self.temp_file:
      self.temp_file.close()


class DataInputDownloader:
  """
  Takes an iterator or a list of api.Data instances as input,
  and has a method for downloading all inputs (currently only images) of that data.
  Has the ability of either writing to a new ZIP archive OR a filesystem directory.
  """

  def __init__(self, data_iterator):
    self.data_iterator = data_iterator
    self.num_inputs = 0
    self.split_prefix = None
    if isinstance(self.data_iterator, DatasetExportReader):
      self.split_prefix = self.data_iterator.split_dir

  def _save_image_to_archive(self, new_archive, hosted_url, name):
    """
    Use PIL ImageFile to return image parsed from the response bytestring (from requests) and append to zip file.
    """
    p = ImageFile.Parser()
    p.feed(requests.get(hosted_url).content)
    image = p.close()
    image_file = BytesIO()
    image.save(image_file, 'JPEG')
    new_archive.writestr(name, image_file.getvalue())

  def _write_image_archive(self, save_path, split):
    """
    Writes the image archive into prefix dir.
    """
    try:
      total = len(self.data_iterator)
    except TypeError:
      total = None
    with zipfile.ZipFile(save_path, "a") as new_archive:
      for data in tqdm(self.data_iterator, desc="Writing image archive", total=total):
        #checks for image
        if data.image.hosted.prefix:
          assert 'orig' in data.image.hosted.sizes
          prefix = data.image.hosted.prefix
          suffix = data.image.hosted.suffix
          hosted_url = f"{prefix}/orig/{suffix}"
          name = suffix.split('/')[-1] + ".jpg"
          full_name = os.path.join(split, name)

          self._save_image_to_archive(new_archive, hosted_url, full_name)
          self.num_inputs += 1

  def _check_output_archive(self, save_path):
    try:
      archive = zipfile.ZipFile(save_path, 'r')
    except zipfile.BadZipFile as e:
      raise e
    assert len(
        archive.namelist()) == self.num_inputs, "Archive has %d inputs | expecting %d inputs" % (
            len(archive.namelist()), self.num_inputs)

  def download_image_archive(self, save_path, split=None):
    """
    Downloads the archive from the URL into an archive of images in the directory format {split}/{image}.
    """
    self._write_image_archive(save_path, split=split or self.split_prefix)
    self._check_output_archive(save_path)


if __name__ == "__main__":
  archive_url = 'https://s3.amazonaws.com/clarifai-data-dumps/prod/app/045342b081ad4b699c5f19adcefed017/dumps/d1dbdf58c65d421b803b7c72535f9e92/exports/clarifai-data-protobuf.zip'
  with DatasetExportReader(archive_url=archive_url) as reader:
    DataInputDownloader(reader).download_image_archive(save_path="output.zip")
