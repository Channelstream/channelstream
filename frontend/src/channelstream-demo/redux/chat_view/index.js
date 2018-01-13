'use strict';

export const types = {
    SET_USER_STATES: 'chatView/SET_USER_STATES',
    SET_CHANNEL_STATES: 'chatView/SET_CHANNEL_STATES',
    DEL_CHANNEL_STATE: 'chatView/DEL_CHANNEL_STATE',
    SET_CHANNEL_MESSAGES: 'chatView/SET_CHANNEL_MESSAGES',
};

export const actions = {
    setChannelStates: (states) => ({
        type: types.SET_CHANNEL_STATES,
        states: states
    }),
    delChannelState: (channel) => ({
        type: types.DEL_CHANNEL_STATE,
        channel: channel
    }),
    setUserStates: (states) => ({
        type: types.SET_USER_STATES,
        states: states
    }),

    setChannelMessages: (messages) => ({
        type: types.SET_CHANNEL_MESSAGES,
        messages: messages
    })
};

const INITIAL_STATE = {
    //mapping of user states for presentation
    users: {states: {}, allIds: {}},
    //mapping of channel configuration
    channels: {states: {}, allIds: {}},
    //what we can subscribe to
    possibleChannels: ['notify', 'pub_chan', 'second_channel'],
    //mapping of channels with messages
    channelMessages: {},
    //message objects
    messages: {messages: {}, allIds: []},
    //what channel are we looking at now
    selectedChannel: 'pub_chan'
};

export const reducer = (state = INITIAL_STATE, action) => {
    if (typeof state === 'undefined') {
        return INITIAL_STATE;
    }
    switch (action.type) {
        case types.SET_CHANNEL_STATES:
            state = {
                ...state,
                channels: {
                    states: {...state.channels.states},
                    allIds: [...state.channels.allIds],
                }
            };
            for (let channelState of Object.entries(action.states)) {
                state.channels.states[channelState[0]] = {
                    name: channelState[1].name,
                    longName: channelState[1].long_name,
                    settings: channelState[1].settings,
                    lastActive: channelState[1].last_active,
                    totalConnections: channelState[1].total_connections,
                    totalUsers: channelState[1].total_users
                };
                if (state.channels.allIds.indexOf(channelState[0]) === -1) {
                    state.channels.allIds.push(channelState[0])
                }
            }
            break;
        case types.DEL_CHANNEL_STATE:
            let newArray = [];
            let foundIndex = state.channels.allIds.indexOf(action.channel);
            if (foundIndex !== -1) {
                newArray = state.channels.allIds.slice();
                newArray.splice(foundIndex, 1);
                delete state.channels.states[action.channel]
            }
            state = {
                ...state,
                channels: {
                    states: {...state.channels.states},
                    allIds: newArray
                }
            };
            break;
        case types.SET_USER_STATES:
            state = {
                ...state,
                users: {
                    states: {...state.users.states},
                    allIds: [...state.users.allIds],
                }
            };
            for (let user of action.states) {
                state.users.states[user.user] = {...user.state};
                if (state.users.allIds.indexOf(user.user) === -1) {
                    state.users.allIds.push(user.user)
                }
            }
            break;
        case types.SET_CHANNEL_MESSAGES:
            state = {
                ...state,
                messages: {messages: {}, allIds: []},
                channelMessages: {...state.channelMessages}
            };
            for (let messageInfo of Object.entries(action.messages)) {
                for (let msg of messageInfo[1]) {
                    state.messages.messages[msg.uuid] = msg;
                    if (!state.channelMessages.hasOwnProperty(messageInfo[0])) {
                        state.channelMessages[messageInfo[0]] = [];
                    }
                    if (state.messages.allIds.indexOf(msg.uuid) === -1) {
                        state.messages.allIds.push(msg.uuid);
                        state.channelMessages[messageInfo[0]].push(msg.uuid);
                    }
                }

            }

            break;
    }
    return state;
};

export default reducer
