#
# Revit Batch Processor
#
# IronPython 3.4 port (Phase 2b). No Py2-specific syntax.
#

import clr
import System
from System.IO import Directory, Path, File

import json_util

TEST_MODE_DATA__SESSION_ID = "sessionId"
TEST_MODE_DATA__REVIT_PROCESS_IDS = "revitProcessIds"


class TestMode:
    def __init__(self, testModeFolderPath):
        self.TestModeFolderPath = testModeFolderPath

    def CreateTestModeFolder(self):
        if not str.IsNullOrWhiteSpace(self.TestModeFolderPath):
            Directory.CreateDirectory(self.TestModeFolderPath)
        if not Directory.Exists(self.TestModeFolderPath):
            raise Exception("ERROR: failed to create the test mode folder!")

    def GetTestModeDataFilePath(self):
        return Path.Combine(self.TestModeFolderPath, "test_mode_data.json")

    def GetTestModeData(self):
        testModeDataFilePath = self.GetTestModeDataFilePath()
        if File.Exists(testModeDataFilePath):
            return json_util.DeserializeToJObject(File.ReadAllText(testModeDataFilePath))
        testModeData = json_util.JObject()
        testModeData[TEST_MODE_DATA__SESSION_ID] = None
        testModeData[TEST_MODE_DATA__REVIT_PROCESS_IDS] = json_util.JArray()
        return testModeData

    def SaveTestModeData(self, testModeData):
        testModeData = json_util.SerializeObject(testModeData, prettyPrint=True)
        File.WriteAllText(self.GetTestModeDataFilePath(), testModeData)

    def WithTestModeData(self, testModeDataAction):
        testModeData = self.GetTestModeData()
        testModeDataAction(testModeData)
        self.SaveTestModeData(testModeData)

    def ExportRevitProcessId(self, revitProcessId):
        def action(testModeData):
            testModeData[TEST_MODE_DATA__REVIT_PROCESS_IDS].Add(revitProcessId)
        self.WithTestModeData(action)

    def ExportSessionId(self, sessionId):
        def action(testModeData):
            testModeData[TEST_MODE_DATA__SESSION_ID] = sessionId
        self.WithTestModeData(action)


def GetSessionId(testModeData):
    return json_util.GetValueFromJValue(testModeData[TEST_MODE_DATA__SESSION_ID])


def GetRevitProcessIds(testModeData):
    return [
        json_util.GetValueFromJValue(revitProcessId)
        for revitProcessId in testModeData[TEST_MODE_DATA__REVIT_PROCESS_IDS]
    ]
