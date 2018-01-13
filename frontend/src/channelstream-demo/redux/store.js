import {createStore, compose, combineReducers, applyMiddleware} from '../../../node_modules/redux/dist/redux';
import logger from '../../../node_modules/redux-logger/dist/redux-logger';
import PolymerRedux from '../../vendor/polymer-redux';

import currentActions from '../../channelstream-admin/redux/current_actions';
import serverInfoView from '../../channelstream-admin/redux/server_info';
import user from './user';
import app from './app';
import chatView from './chat_view';
const combinedReducers = combineReducers({app, user, currentActions, chatView, adminView: serverInfoView});

const store = createStore(combinedReducers, {}, applyMiddleware(logger));
window.ReduxStore = store;
// Create the PolymerRedux mixin
const ReduxMixin = PolymerRedux(store);
export {ReduxMixin};
