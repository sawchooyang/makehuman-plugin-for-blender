#!/usr/bin/python

from namespace import NameSpace

import getpath
import os
import sys
import re
import codecs
import shutil

class Assets(NameSpace):
    """This namespace wraps all calls that are related to reading and managing assets."""

    def __init__(self,api):
        self.api = api
        NameSpace.__init__(self)
        self.trace()

        self.extensionToType = dict()
        self.extensionToType[".mhmat"] = "material"
        self.extensionToType[".mhclo"] = "proxy"
        self.extensionToType[".proxy"] = "proxy"
        self.extensionToType[".target"] = "target"
        self.extensionToType[".mhm"] = "models"
        
        self.genericExtraKeys = ["tag"]
        self.genericKeys = ["name","description"]
        self.genericCommentKeys = ["license","homepage","author"]

        self.proxyKeys = [
            "uuid",
            "basemesh",
            "obj_file",
            "max_pole",
            "z_depth",
            "x_scale",
            "y_scale",
            "z_scale"
        ]

        self.materialKeys = [
            "diffuseColor",
            "specularColor",
            "emissiveColor",
            "ambientColor",
            "diffuseTexture",
            "bumpMapTexture",
            "normalMapTexture",
            "displacementMapTexture",
            "specularMapTexture",
            "transparencyMapTexture",
            "aoMapTexture",
            "diffuseIntensity",
            "bumpMapIntensity",
            "normalMapIntensity",
            "displacementMapIntensity",
            "specularMapIntensity",
            "transparencyMapIntensity",
            "aoMapIntensity",
            "shininess",
            "opacity",
            "translucency",
            "shadeless",
            "wireframe",
            "transparent",
            "alphaToCoverage",
            "backfaceCull",
            "depthless",
            "castShadows",
            "receiveShadows",
            "alphaToCoverage"
        ] # There are also SSS settings, but I don't know if those actually works


    def _parseGenericAssetInfo(self,fullPath):

        info = dict()

        fPath, ext = os.path.splitext(fullPath)
        basename = os.path.basename(fullPath)

        info["type"] = self.extensionToType[ext]
        info["absolute path"] = fullPath
        info["extension"] = ext
        info["basename"] = basename
        info["rawlines"] = []
        info["location"] = os.path.dirname(fullPath)
        info["parentdir"] = os.path.basename(info["location"])

        with codecs.open(fullPath,'r','utf8') as f:
            contents = f.readlines()
            for line in contents:
                info["rawlines"].append(re.sub(r"[\x0a\x0d]+",'',line))

        info["rawkeys"] = []
        info["rawcommentkeys"] = []

        for line in info["rawlines"]:
            m = re.match(r"^([a-zA-Z_]+)\s+(.*)$",line)
            if(m):
                info["rawkeys"].append([m.group(1),m.group(2)])
            m = re.match(r"^#\s+([a-zA-Z_]+)\s+(.*)$",line)
            if(m):
                info["rawcommentkeys"].append([m.group(1),m.group(2)])
        
        for genericExtraKeyName in self.genericExtraKeys:
            info[genericExtraKeyName] = set()
            for rawkey in info["rawkeys"]:
                rawKeyName = rawkey[0]
                rawKeyValue = rawkey[1]
                if rawKeyName == genericExtraKeyName:
                    info[genericExtraKeyName].add(rawKeyValue)

        for genericKeyName in self.genericKeys:
            info[genericKeyName] = None
            for rawkey in info["rawkeys"]:
                rawKeyName = rawkey[0]
                rawKeyValue = rawkey[1]
                if rawKeyName == genericKeyName:
                    info[genericKeyName] = rawKeyValue

        for genericCommentKeyName in self.genericCommentKeys:
            info[genericCommentKeyName] = None
            for commentKey in info["rawcommentkeys"]:
                commentKeyName = commentKey[0]
                commentKeyValue = commentKey[1]
                if commentKeyName == genericCommentKeyName:
                    info[commentKeyName] = commentKeyValue

        return info

    def _parseProxyKeys(self,assetInfo):
        for pk in self.proxyKeys:
            assetInfo[pk] = None
            for k in assetInfo["rawkeys"]:
                key = k[0]
                value = k[1]
                if key == pk:
                    assetInfo[pk] = value

    def _parseMaterialKeys(self,assetInfo):
        for pk in self.materialKeys:
            assetInfo[pk] = None
            for k in assetInfo["rawkeys"]:
                key = k[0]
                value = k[1]
                if key == pk:
                    assetInfo[pk] = value


    def _parseMaterials(self,assetInfo):
        if not "materials" in assetInfo:
            assetInfo["materials"] = []
        for k in assetInfo["rawkeys"]:
            key = k[0]
            value = k[1]
            if key == "material":
                assetInfo['materials'].append(value)

    def _addPertinentKeyInfo(self,assetInfo):

        pertinentKeys = list(self.genericKeys)
        pertinentExtraKeys = list(self.genericExtraKeys)
        pertinentCommentKeys = list(self.genericCommentKeys)

        if assetInfo["type"] == "proxy":
            pertinentKeys.extend(self.proxyKeys)

        if assetInfo["type"] == "material":
            pertinentKeys.extend(self.materialKeys)

        assetInfo["pertinentKeys"] = pertinentKeys
        assetInfo["pertinentExtraKeys"] = pertinentExtraKeys
        assetInfo["pertinentCommentKeys"] = pertinentCommentKeys


    def openAssetFile(self, path, strip = False):
        """Opens an asset file and returns a hash describing it"""
        fullPath = self.api.locations.getUnicodeAbsPath(path)
        if not os.path.isfile(fullPath):
            return None
        info = self._parseGenericAssetInfo(fullPath)

        self._addPertinentKeyInfo(info)

        if info["type"] == "proxy":
            self._parseProxyKeys(info)

        if info["type"] == "material":
            self._parseMaterialKeys(info)

        thumbPath = os.path.splitext(path)[0] + ".thumb"

        if os.path.isfile(thumbPath):
            info["thumb_path"] = thumbPath
        else:
            info["thumb_path"] = None

        if strip:
            info.pop("rawlines",None)
            info.pop("rawkeys",None)
            info.pop("rawcommentkeys",None)

        return info


    def writeAssetFile(self, assetInfo, createBackup = True):
        if not assetInfo:
            print "Cannot use None as assetInfo"
            return False

        ap = assetInfo["absolute path"]
        bak = ap + ".bak"

        if createBackup and os.path.isfile(ap):
            shutil.copy(ap,bak)

        print ap

        with codecs.open(ap,'w','utf8') as f:
            for line in assetInfo["rawlines"]:
                allowWrite = True
                m = re.match(r"^([a-zA-Z_]+)\s+(.*)$",line)
                if m:
                    key = m.group(1)
                    if key in assetInfo["pertinentKeys"]:
                        print "exists"
                        allowWrite = False
                        if not assetInfo[key] is None:
                            f.write(key + " " + assetInfo[key] + "\x0a")

                m = re.match(r"^#\s+([a-zA-Z_]+)\s+(.*)$",line)
                if m:
                    key = m.group(1)
                    if key in assetInfo["pertinentCommentKeys"]:
                        allowWrite = False
                        if not assetInfo[key] is None:
                            f.write("# " + key + " " + assetInfo[key] + "\x0a")
                if allowWrite:
                    f.write(line + "\x0a")
        return True