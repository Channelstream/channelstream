'use strict';

export const types = {
    SET_CHANNEL_MESSAGES: 'chatView/SET_CHANNEL_MESSAGES',
    DELETE_CHANNEL_MESSAGES: 'chatView/DELETE_CHANNEL_MESSAGES',
    EDIT_CHANNEL_MESSAGES: 'chatView/EDIT_CHANNEL_MESSAGES',
};

export const actions = {
    setChannelMessages: (messages) => ({
        type: types.SET_CHANNEL_MESSAGES,
        messages: messages
    }),
    deleteChannelMessages: (message_ids) => ({
        type: types.DELETE_CHANNEL_MESSAGES,
        message_ids: message_ids
    }),
    editChannelMessages: (messages) => ({
        type: types.EDIT_CHANNEL_MESSAGES,
        messages: messages
    }),
};

const INITIAL_STATE = {
    //mapping of channels with messages
    channelMessages: {},
    //message objects
    messages: {},
    allIds: []
};


export const reducer = (state = INITIAL_STATE, action) => {
    if (typeof state === 'undefined') {
        return INITIAL_STATE;
    }
    let newChannelMessages = {};
    let newMessages = {};
    switch (action.type) {
        case types.SET_CHANNEL_MESSAGES:
            for (let key in state.channelMessages){
                newChannelMessages[key] = [...state.channelMessages[key]];
            }
            state = {
                messages: {...state.messages},
                allIds: [...state.allIds],
                channelMessages: newChannelMessages
            };
            for (let message of action.messages) {
                state.messages[message.uuid] = message;
                if (!state.channelMessages.hasOwnProperty(message.channel)) {
                    state.channelMessages[message.channel] = [];
                }
                if (state.allIds.indexOf(message.uuid) === -1) {
                    state.allIds.push(message.uuid);
                    state.channelMessages[message.channel].push(message.uuid);
                }
            }
            break;
        case types.EDIT_CHANNEL_MESSAGES:
            newMessages = {...state.messages};
            for(let message of action.messages){
                if (newMessages.hasOwnProperty(message.uuid)){
                    newMessages[message.uuid] = {...newMessages[message.uuid], ...message}
                }
            }
            state = {
                messages: newMessages,
                allIds: [...state.allIds],
                channelMessages: {...state.channelMessages}
            };
            break;

        case types.DELETE_CHANNEL_MESSAGES:
            for (let key in state.channelMessages){
                newChannelMessages[key] = [...state.channelMessages[key].filter(uuid => action.message_ids.indexOf(uuid) === -1)];
            }
            for (let uuid in state.messages){
                if (action.message_ids.indexOf(uuid) === -1){
                    newMessages[uuid] = state.messages[uuid]
                }
            }
            state = {
                messages: newMessages,
                allIds: [...state.allIds.filter(uuid => action.message_ids.indexOf(uuid) === -1)],
                channelMessages: newChannelMessages
            };
            break;
    }
    return state;
};

export default reducer
