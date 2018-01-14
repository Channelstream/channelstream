'use strict';

export const types = {
    SET_CHANNEL_STATES: 'chatView/SET_CHANNEL_STATES',
    DEL_CHANNEL_STATE: 'chatView/DEL_CHANNEL_STATE',
};

export const actions = {
    setChannelStates: (states) => ({
        type: types.SET_CHANNEL_STATES,
        states: states
    }),
    delChannelState: (channel) => ({
        type: types.DEL_CHANNEL_STATE,
        channel: channel
    })
};


const INITIAL_STATE = {states: {}, allIds: {}};

export const reducer = (state = INITIAL_STATE, action) => {
    if (typeof state === 'undefined') {
        return INITIAL_STATE;
    }
    switch (action.type) {
        case types.SET_CHANNEL_STATES:
            state = {
                states: {...state.states},
                allIds: [...state.allIds]
            };
            for (let channelState of Object.entries(action.states)) {
                state.states[channelState[0]] = {
                    name: channelState[1].name,
                    longName: channelState[1].long_name,
                    settings: channelState[1].settings,
                    lastActive: channelState[1].last_active,
                    totalConnections: channelState[1].total_connections,
                    totalUsers: channelState[1].total_users
                };
                if (state.allIds.indexOf(channelState[0]) === -1) {
                    state.allIds.push(channelState[0])
                }
            }
            break;
        case types.DEL_CHANNEL_STATE:
            let newArray = [];
            let foundIndex = state.allIds.indexOf(action.channel);
            if (foundIndex !== -1) {
                newArray = state.allIds.slice();
                newArray.splice(foundIndex, 1);
                delete state.states[action.channel]
            }
            state = {
                states: {...state.states},
                allIds: newArray
            };
            break;
    }
    return state;
};

export default reducer
