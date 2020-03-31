# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


"""Checks the consistency between the zotfile-managed directory and the database"""

import sqlite3
import sys
import unicodedata
import fnmatch
import os
import pathlib
import re
from pathlib import Path
from sys import platform


def get_db_set(database, zotDir):
    """ Return pdfs names that are content of the sqlite zotero database
    
    Parameters
    ----------
    database : Path object
        Path to Zotero database
    zotDir : Path object
        Path to Zotfile folder

    Returns
    -------
    database_set: set
        Set with pdf's names  to which Zotero database points to 
    """

    conn = sqlite3.connect(database)

    db_c = conn.execute(
        'select path from itemAttachments where linkMode = 2 or linkMode = 3 and contentType = "application/pdf"')
    db_d = db_c.fetchall()

    db_l = []
    for i in range(len(db_d)):
        try:
            # Ignore all kind of errors wholesale, i.e. duck typing
            item = db_d[i][0]
            if not item.lower().endswith(".pdf"):
                continue
            if item.count('attachments:') > 0: # relative path
                item = item.replace('attachments:', "")
            else: # absolute path
                item = str(pathlib.Path(item).relative_to(zotDir))
        except:
            # file is not in zotfile directory
            continue

        db_l.append(unicodedata.normalize("NFD", item))
        
    database_set = set(db_l)
    return database_set


def get_dir_set(zotDir):
    """ Return pdfs names from given folder
    
    Parameters
    ----------
    dir_path : Path object
        Path to dropbox folder in which files are stored
    
    Returns
    -------
    dir_set: set
        Set with pdf's names contained in the folder
    """

    rule = re.compile(fnmatch.translate("*.pdf"), re.IGNORECASE)
    matches = []
    for root, dirnames, filenames in os.walk(zotDir):
        for filename in [name for name in filenames if rule.match(name)]:
            matches.append(os.path.join(root, filename))

    fs = [str(pathlib.Path(f).relative_to(zotDir)) for f in matches]
    fs = [unicodedata.normalize("NFD", x) for x in fs]
    zotfile_set = set(fs)
    return zotfile_set


def create_dir(tempDir):
    """ Create directory on given path """
    if not os.path.exists(tempDir):
        os.mkdir(tempDir)
        print("Directory " , tempDir ,  " Created ")
    else:    
        print("Directory " , tempDir ,  " already exists")


def database_vs_zotfile(database, zotDir):
    """ Get and print differences between Zotero database and Zotfile folder
    
    Parameters
    ----------
    database : Path object
        Path to Zotero database
    zotDir : Path object
        Path to Zotfile folder

    
    Returns
    -------
    db_not_dir : set
        set of pdf recorded in sqlite file not in Zotfile folder
    dir_not_db : set 
        set of files in Zotfile folder but not in Zotero sqlite database

    """
    db_set = get_db_set(database, zotDir)
    dir_set = get_dir_set(zotDir)

    db_not_dir = db_set.difference(dir_set)
    dir_not_db = dir_set.difference(db_set)

    print(
        f"There were {len(db_not_dir)}/{len(db_set)} files in DB but not in zotfile directory:")
    for f in sorted(db_not_dir):
        print("   " + f)

    print("\n")
    print(
        f"There were {len(dir_not_db)}/{len(dir_set)} files in zotfile directory but not in DB:")
    for f in sorted(dir_not_db):
        print("   " + f)
    return db_not_dir, dir_not_db, db_set, dir_set

def move_zofiles_not_in_database(database, zotDir, tempDir):
    """ Move files that are not in Zotero database, but in Zotfile dir to tempDir """

    db_not_dir, dir_not_db , db_set, dir_set = database_vs_zotfile(database, zotDir)

    # Create target Directory if don't exist
    create_dir(tempDir)
    for file in dir_not_db:
        try:
            print(zotDir / file)
            print("i")
            Path( zotDir / file).rename(tempDir / file)
        except:
           print(f"{file} not found")




if platform == "linux" or platform == "linux2":# on linux
    userPath = Path("/home/daniel/")
elif platform == "darwin":#on mac
    userPath = Path("/Users/daniel/")
    
database = userPath / "Zotero/zotero.sqlite"
zotDir =  userPath / "Dropbox/Zotero/"
tempDir    =   userPath / "temp_files/"

#move_zofiles_not_in_database(database, zotDir, tempDir)

# %%
ZoteroStorage = userPath / "Zotero/storage"
StorageTemp =  userPath /  "storage_temp"


def move_zotero_storage_files(ZoteroStorage, StorageTemp, zotDir):
    """ Move files  from zoteto storage folders"""
    create_dir(StorageTemp)    
    for path in ZoteroStorage.rglob('*.pdf'):
        print(path.name)
        path.rename(StorageTemp / path.name)
        
    zot_temp_set = get_dir_set(StorageTemp)
    zot_not_zotFile = zot_temp_set.difference(get_dir_set(zotDir))
    for file in zot_not_zotFile:
                 print(file)

move_zotero_storage_files(ZoteroStorage, StorageTemp, zotDir)

# files in Zotero default folder but not in Zoffile folder  


#         
#         if zot:
#             z =  "/home/daniel/Zotero/temp"
#            
#     else:
#         main(sys.argv[1], sys.argv[2])
