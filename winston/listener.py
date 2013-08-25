import gobject
import pygst
pygst.require('0.10')
gobject.threads_init()
import gst

class Listener(object):
    """
    Listens, understands and processes speeches using the
    python-gstreamer plugin.

    This class is loosely based on the example from the anemic
    official pocketsphinx documentation.
    """
    def __init__(self, interpreters=[], fsg_path=None, dict_path=None, start=True):
        """
        Initialize the listener
        """
        # Set the path to the finite state grammar (FSG) file
        # Don't have an FSG? Use sphinx_jsgf2fsg, or set it to None
        # to run pocketsphinx without a grammar (not recommended).
        self.fsg_path = fsg_path
        self.dict_path = dict_path

        # Init gstreamer
        self.init_gstreamer()

        # Set the command interpreters
        self.interpreters = interpreters

        # Start listening
        if start:
            self.start()

    def init_gstreamer(self):
        # Get the pipeline
        self.pipeline = gst.parse_launch('gconfaudiosrc ! audioconvert ! audioresample '
                                         + '! vader name=vad auto_threshold=true '
                                         + '! pocketsphinx name=asr ! fakesink')
        asr = self.pipeline.get_by_name('asr')

        # Bind the pipeline results
        # asr.connect('partial_result', self.asr_partial_result)
        asr.connect('result', self.asr_result)

        # Load the grammar file unless it was deactivated
        if self.fsg_path:
            asr.set_property("fsg", self.fsg_path)

        if self.dict_path:
            asr.set_property("dict", self.dict_path)

        # This tells the asr that it's ready to run
        asr.set_property('configured', True)

        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        
        self.pipeline.set_state(gst.STATE_PAUSED)

    def asr_result(self, asr, parsed_text, utterance_id):
        """
        Receives a result from the pipeline, and forwards the parsed
        text to process_result.
        """
        self.pause()
        self.process_result(parsed_text)
        self.start()

    def start(self):
        self.pipeline.set_state(gst.STATE_PLAYING)

    def pause(self):
        self.pipeline.set_state(gst.STATE_PAUSED)

    def process_result(self, parsed_text):
        """
        Sends the command string to all interpreters for dispatching.
        """
        for interpreter in self.interpreters:
            interpreter.match(parsed_text)