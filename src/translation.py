# Copyright 2024 ASL19 Organization
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json

class Translation(object):
    """
    Class to handle multiple languages for the bot
    """
    def __init__(self, language, language_file):

        self.language = language

        self.texts = {}
        try:
            with open(language_file) as lang_file:
                self.texts = json.load(lang_file)
        except IOError as error:
            raise ObjectCreationFailed

    def text(self, name):
        """
        Returns the translation for text

        :param name: name of the text
        :return: Text in the language set in the object
        """
        return self.texts[name][self.language]
