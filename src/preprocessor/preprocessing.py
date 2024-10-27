import os
import json
import pandas as pd
from typing import List, Union
from loguru import logger
import pandas as pd
import pathlib


## Set of helper functions that support data preprocessing 
class FileIO:
    '''
    Convenience class for saving and loading data in parquet and json formats 
    to/from disk.
    '''

    @classmethod
    def save_as_parquet(cls,
                        file_path: str, 
                        data: Union[List[dict], pd.DataFrame], 
                        overwrite: bool=False) -> None:
        '''
        Saves DataFrame to disk as a parquet file.  Removes the index. 

        Args:
        -----
        file_path : str
            Output path to save file, if not included "parquet" will be appended
            as file extension.
        data : Union[List[dict], pd.DataFrame]
            Data to save as parquet file. If data is a list of dicts, it will be
            converted to a DataFrame before saving.
        overwrite : bool
            Overwrite existing file if True, otherwise raise FileExistsError.
        '''
        if isinstance(data, list):
           data = cls._convert_toDataFrame(data)
        if not file_path.endswith('parquet'):
            file_path = cls._rename_file_extension(file_path, 'parquet')
        cls._check_file_path(file_path, overwrite=overwrite)
        data.to_parquet(file_path, index=False)
        logger.info(f'DataFrame saved as parquet file here: {file_path}')
        
    def _convert_toDataFrame(data: List[dict]) -> pd.DataFrame:
        return pd.DataFrame().from_dict(data)

    def _rename_file_extension(file_path: str, extension: str):
        '''
        Renames file with appropriate extension if file_path
        does not already have correct extension.
        '''
        prefix = os.path.splitext(file_path)[0]
        file_path = prefix + '.' + extension
        return file_path

    def _check_file_path(file_path: str, overwrite: bool) -> None:
        '''
        Checks for existence of file and overwrite permissions.
        '''
        if os.path.exists(file_path) and overwrite == False:
            raise FileExistsError(f'File by name {file_path} already exists, try using another file name or set overwrite to True.')
        elif os.path.exists(file_path):
            os.remove(file_path)
        else: 
            file_name = os.path.basename(file_path)
            dir_structure = file_path.replace(file_name, '')
            pathlib.Path(dir_structure).mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def load_parquet(file_path: str, verbose: bool=True) -> List[dict]:
        '''
        Loads parquet from disk, converts to pandas DataFrame as intermediate
        step and outputs a list of dicts (docs).
        '''
        df = pd.read_parquet(file_path)
        vector_labels = ['content_vector', 'image_vector', 'content_embedding', 'keywords']
        for label in vector_labels:
            if label in df.columns:
                df[label] = df[label].apply(lambda x: x.tolist())
        if verbose:
            memory_usage = round(df.memory_usage().sum()/(1024*1024),2)
            print(f'Shape of data: {df.values.shape}')
            print(f'Memory Usage: {memory_usage}+ MB')
        list_of_dicts = df.to_dict('records')
        return list_of_dicts
    
    @staticmethod
    def load_json(file_path: str) -> list[dict]:
        '''
        Loads json file from disk.
        '''
        with open(file_path) as f:
            data = json.load(f)
        return data
    
    @classmethod
    def save_as_json(cls, 
                     file_path: str, 
                     data: Union[List[dict], dict], 
                     indent: int=4,
                     overwrite: bool=False
                     ) -> None:
        '''
        Saves data to disk as a json file. Data can be a list of dicts or a single dict.
        '''
        if not file_path.endswith('json'):
            file_path = cls._rename_file_extension(file_path, 'json')
        cls._check_file_path(file_path, overwrite=overwrite)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=indent)
        logger.info(f'Data saved as json file here: {file_path}')

class Utilities: 

    def create_video_url(self, video_id: str, playlist_id: str):
        '''
        Creates a hyperlink to a video episode given a video_id and playlist_id.

        Args:
        -----
        video_id : str
            Video id of the episode from YouTube
        playlist_id : str
            Playlist id of the episode from YouTube
        '''
        return f'https://www.youtube.com/watch?v={video_id}&list={playlist_id}'

    def convert_raw_data(self, raw_data: dict | list[dict]) -> list[dict]:
        '''
        Converts raw YouTube json to correct format for 
        indexing on Weaviate. i.e. drops unused fields, 
        and coerces data types. 
        '''
        drops = ['channelId', 'isOwnerViewing', 'isCrawlable', 'allowRatings', \
                 'author', 'isPrivate', 'isUnpluggedCorpus', 'isLiveContent']
        if not isinstance(raw_data, dict):   
            raise TypeError('Input data must be a dictionary.')
        data = [v for k, v in raw_data.items() if k not in drops]
        for d in data:
            d['thumbnail_url'] = d['thumbnail']['thumbnails'][1].get('url')
            d['lengthSeconds'] = int(d['lengthSeconds'])
            d['viewCount'] = int(d['viewCount'])
            del d['thumbnail']
            for field in drops:
                del d[field]
        return data
    