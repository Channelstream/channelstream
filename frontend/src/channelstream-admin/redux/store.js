import {createStore, compose, combineReducers, applyMiddleware} from 'redux/dist/redux';
import logger from 'redux-logger/dist/redux-logger';

import serverInfo from './server_info';
import currentActions from './current_actions';


const combinedReducers = combineReducers({serverInfo, currentActions});

const store = createStore(combinedReducers, {}, applyMiddleware(logger));

export {store};
