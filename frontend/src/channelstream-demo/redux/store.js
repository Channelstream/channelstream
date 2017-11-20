import {createStore, compose, combineReducers, applyMiddleware} from '../../../node_modules/redux/dist/redux';
import logger from '../../../node_modules/redux-logger/dist/redux-logger';
import PolymerRedux from '../../vendor/polymer-redux';

import currentActions from '../../channelstream-admin/redux/current_actions';


const combinedReducers = combineReducers({currentActions});

const store = createStore(combinedReducers, {}, applyMiddleware(logger));
window.ReduxStore = store;
// Create the PolymerRedux mixin
const ReduxMixin = PolymerRedux(store);

export {ReduxMixin};
