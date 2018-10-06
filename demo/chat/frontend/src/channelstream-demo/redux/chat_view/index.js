'use strict';

import {combineReducers} from '../../../../node_modules/redux/dist/redux';
import channelsReducer from './channels.js';
import usersReducer from './users.js';
import messagesReducer from './messages.js';
import uiReducer from './ui.js';

const INITIAL_STATE = {
    //mapping of user states for presentation
    users: undefined,
    //mapping of message information
    messages: undefined,
    //mapping of channel configuration
    channels: undefined,
    //what channel are we looking at now
    ui: undefined
};

export const reducer = (state = INITIAL_STATE, action) => {
    if (typeof state === 'undefined') {
        return INITIAL_STATE;
    }
    state = {
        ...state,
        channels: channelsReducer(state.channels, action),
        messages: messagesReducer(state.messages, action),
        users: usersReducer(state.users, action),
        ui: uiReducer(state.ui, action)
    };
    return state;
};

export default reducer
