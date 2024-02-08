from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.factory import Factory
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup

import os

class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)


class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)


class Root(FloatLayout):
    RecordingState = False
    loadfile = ObjectProperty(None)

    def dismiss_popup(self):
        self._popup.dismiss()

    def show_choose(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="Choose directory", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def toggle_recordState(self):
        print("Recording will be toggled ...")
        if RecordingState:
            self.ids["label_state"].text = "Recording stopped"
            RecordingState = False
        else:
            self.ids["label_state"].text = "Recording is active"
            RecordingState = True
        
    def load(self, path, filename):
        print('Selected path: %s' % (path))
        self.ids["label_path"].text = path
        self.dismiss_popup()


class ExampleEditor(App):
    pass


Factory.register('Root', cls=Root)
Factory.register('LoadDialog', cls=LoadDialog)


if __name__ == '__main__':
    ExampleEditor().run()