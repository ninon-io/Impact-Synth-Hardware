"""

 ~ Neurorack project ~
 Menu : Set of classes for handling the menus
 
 This file defines the main operations for graphical menus
 The functions here will be used for the LCD display.
 Parts of this code have been inspired by the great piControllerMenu code:
     https://github.com/Avanade/piControllerMenu
 
 Author               :  Ninon Devis, Philippe Esling, Martin Vert
                        <{devis, esling}@ircam.fr>
 
 All authors contributed equally to the project and are listed aphabetically.

"""
from .graphics import Graphic, TextGraphic, SliderGraphic
from .config import config
from .menu_functions import model_play, model_select, model_reload, model_benchmark
from .menu_functions import params_volume, params_stereo, params_range
from .menu_function import assign_cv, assign_button, assign_rotary
from .menu_function import admin_stats, about

class MenuItem(Graphic):    
    '''
    Represents a menu item
    '''
    
    function_dispatcher = {
        'model_play': model_play,
        'model_select': model_select,
        'model_reload': model_reload,
        'model_benchmark': model_benchmark,
        'params_volume': params_volume,
        'params_stereo': params_stereo,
        'params_range': params_range,
        'assign_cv': assign_cv,
        'assign_button': assign_button,
        'assign_rotary': assign_rotary,
        'admin_stats': admin_stats,
        'about': about
    }

    #region constructor
    def __init__(self, 
                 title: str,
                 type: int, 
                 command: str, 
                 confirm: bool = False):
        """
            Initializes a new instance of the Command class
            Parameters:
                type:       int
                            The type of menu item. 
                command:    str
                            The actual command to execute.
                confirm:    bool
                            True to require confirmation before the command is executed, false otherwise. 
        """
        self._title = title
        self._type: int = type
        self._command: str = command
        self._output: str = ''
        self._confirm: bool = confirm
        self._running: bool = False
        self._graphic: Graphic = None
        if (self._type == 'menu' or self._type == 'shell' or self._type == 'function'):
            self._graphic = TextGraphic(title)
        elif (self._type == 'slider'):
            self._graphic = SliderGraphic(title, None)
        elif (self._type == 'list'):
            self._graphic = TextGraphic(title)
            
    def render(self, ctx):
        return self._graphic.render(ctx)
    
    def get_height(self):
        return self._graphic.get_height()
    
    def get_width(self):
        return self._graphic.get_width()
    
    @staticmethod
    def create_item(title, data):
        """
            Deserialized a command from YAML. 
            Parameters:
                data:   object
                        Representation of the Command data.
            Returns:
                Instance of Command
        """
        if "type" not in data.keys() or (data["type"] not in config.menu.accepted_types):
            message = "Menu item is of unexpected type " + data["type"]
            raise Exception(message)
        if "command" not in data.keys() or data["command"] == "":
            message = "Could not find attribute command"
            raise Exception(message)
        command = MenuItem(
            title,
            type = data["type"],
            command = data["command"],
            confirm = data["confirm"] if "confirm" in data.keys() else False
          )
        return command
    
    def run(self, state, params=None, confirmed=config.menu.confirm_cancel):
        """
            Runs the command.
            Parameters:
                display:    Display
                            Reference to a Display instance. This can be NONE if Command.Type is COMMAND_SHELL
                confirmed:  int
                            Optional. Pass CONFIRM_OK to indicate the command has been confirmed. 
        """
        print('[Pushed command ' + self._title)
        if self._confirm and self._confirmation_handler is not None and confirmed == config.menu.confirm_cancel:
            self._confirmation_handler(self)
        else:
            self._running = True
            if self._type == 'function':
                self.function_dispatcher[self._command](self, state, params)
            elif self._type == 'shell':
                if self.__spinHandler is not None: self.__spinHandler(True)
                try:
                    #breakpoint()
                    self.__output = subprocess.check_output(self.__command, shell=True,  cwd=self.__cwd).decode()
                    self.__returnCode = 0
                except subprocess.CalledProcessError as e:
                    self.__output = e.output.decode()
                    self.__returnCode = e.returncode
                    logging.exception(e)
                except Exception as e:
                    self.__output = str(e)
                    self.__returnCode = -1000
                    logging.exception(e)
                if self.__spinHandler is not None: self.__spinHandler(False)
                if self.__outputHandler is not None: self.__outputHandler(self.__command, self.__returnCode, self.__output)
                self.__running = False
    #endregion

    #region public class (static) methods
    

class MenuBar():
    def __init__(self):
        pass

if __name__ == '__main__':
    menu = Menu('../menu.yaml')
    