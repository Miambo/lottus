import abc
import json
import os.path
import os
import lottus.helpers as helpers

class Lottus(object):
    '''
        Represents the Lottus application.
    '''
    def __init__(self, app_name, initial_menu, menus, session_bag):
        '''
            Represents the Lottus application. It receives the name of the application, 
            the initial menu, the menus and a session bag. The session bag acts as the storage
            for Lottus sessions.
        '''
        self.initial_menu = initial_menu
        self._app_name = app_name
        self._menus = menus
        self._mapped_services = {}
        self._session_bag = session_bag

    def process_menu(self, menu_name, session, request):
        '''
            Processes the request provided. It receives the menu_name and the session
            and the request
        '''
        processor = self._get_menu_name_processor(menu_name)

        if processor:
            menu = self.get_menu(menu_name)
            menu = helpers.do_non_auto_process_menu(menu, processor, session, request)
        else:
            menu = self.get_menu(menu_name)

            if not helpers.is_menu_a_form(menu):
                menu['message'] = "Invalid menu selected"
            elif not helpers.is_active_menu(menu):
                menu['message'] = "Invalid operation selected"
            elif helpers.is_auto_processable_menu(menu):
                menu = self.do_auto_process_menu(menu, session, request)
            else:
                menu['message'] = "Cannot find any processor for selected menu"

        session['location'] = menu['name']
        return menu

    def get_menu(self, menu_name):
        '''
            Receives parameter menu_name and returns the menu
        '''
        return self._menus.get(menu_name)

    def do_auto_process_menu(self, menu, session, request):
        '''
            Processes menus marked as auto_processed = True. It receives the menu,
            the session and the request
        '''
        if menu and 'required' in menu:
            required = menu['required']
            if 'in_options' in required and required['in_options']:
                opt = helpers.get_option(request, menu['options'])
                if opt:
                    if 'value' in opt:
                        session['parameters'][required['var']] = opt['value']
                    else:
                        session['parameters'][required['var']] = opt['option']
            else:
                session["parameters"][required["var"]] = request

            if 'next_menu' in required:
                menu = self.get_menu(required['next_menu'])
                menu = helpers.menu_add_parameters(menu, session)
                return menu

        if menu and 'options' in menu:
            option = helpers.get_option(request, menu['options'])

            if not option:
                if not 'Please select a valid option' in menu['message']:
                    menu['message'] = f'Please select a valid option\n{menu["message"]}'
                else:
                    menu['message'] = 'Please select a valid option'
            elif 'menu' in option:
                menu = self.get_menu(option['menu'])
            else:
                menu['message'] = 'Cannot find menu for option'

        menu = helpers.menu_add_parameters(menu, session)
        return menu


    def _get_menu_name_processor(self, menu_name):
        '''
            Returns the processor for menu_name
        '''
        if menu_name in self._mapped_services:
            return self._mapped_services[menu_name]

        return None

    def handle_request(self, request):
        '''
            Handles all ussd request
        '''
        session = self._session_bag.get_session(request['cell_number'], request['session'])
        if not session:
            session = self._session_bag.create_new_session(request['cell_number'], request['session'])
            session['location'] = self.initial_menu
            menu = self.get_menu(self.initial_menu)
            self._session_bag.save_session(session)
        else:
            menu = self.process_menu(session['location'], session, request['request_str'])
            self._session_bag.update_session(session)

        return helpers.beautify_menu(menu)

    def location(self, menu_name):
        '''
            A decorator that is used to register a new processor for a menu_name
        '''
        def decorator(f):
            self.add_location_menu_name(menu_name, f)
            return f
        return decorator

    def add_location_menu_name(self, menu_name, f):
        '''
        '''
        self._mapped_services[menu_name] = f

class Session(object):
    '''
    '''
    def __init__(number, cell_number):
        '''
        '''
        self._location = None
        self._cell_number = None
        self._number = None
        self._parameters = {}

    def set_location(location):
        '''
        '''
        self._location = location

    def add_variable(name, value):
        '''
        '''
        self._parameters[name] = value


class Menu(object):
    '''
    '''
    def __init__(name, message = None, title = None, type="FORM"):
        '''
        '''
        self.name = name
        self.message = "" if message is None else message
        self.title = "" if title is None else title
        self.options = {}
        self.type = "FORM"
        self.auto_process = True
        self.active = True


class Option(object):
    '''
    '''
    def __init__(name, display, menu):
        self._name = name
        self._display = display
        self._menu = menu
        self._active = True


class Request(object):
    '''
    '''
    def __init__(self, cell_number, request_str, session):
        '''
        '''
        self.cell_number = cell_number
        self.request_str = request_str
        self.session = session


class USSDSessionBag:
    '''
    '''
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_session(self, msisdn, session):
        '''
        '''
        pass

    @abc.abstractmethod
    def add_session(self, session):
        '''
        '''
        pass

    @abc.abstractmethod
    def save_session(self, session):
        '''
        '''
        pass

    @abc.abstractmethod
    def update_session(session):
        '''
        '''
        pass

    def create_new_session(self, msisdn, session):
        '''
        '''
        x = {'location': 'LOGIN', 'msisdn':  msisdn, 'session': session, 'parameters': {}}
        self.add_session(x)

        return x

