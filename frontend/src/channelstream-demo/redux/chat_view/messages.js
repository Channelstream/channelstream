'use strict';

export const types = {
    SET_CHANNEL_MESSAGES: 'chatView/SET_CHANNEL_MESSAGES',
    DELETE_CHANNEL_MESSAGES: 'chatView/DELETE_CHANNEL_MESSAGES',
};

export const actions = {
    setChannelMessages: (messages) => ({
        type: types.SET_CHANNEL_MESSAGES,
        messages: messages
    }),
    deleteChannelMessages: (message_ids) => ({
        type: types.DELETE_CHANNEL_MESSAGES,
        message_ids: message_ids
    })
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
            for (let messageInfo of Object.entries(action.messages)) {
                for (let msg of messageInfo[1]) {
                    state.messages[msg.uuid] = msg;
                    if (!state.channelMessages.hasOwnProperty(messageInfo[0])) {
                        state.channelMessages[messageInfo[0]] = [];
                    }
                    if (state.allIds.indexOf(msg.uuid) === -1) {
                        state.allIds.push(msg.uuid);
                        state.channelMessages[messageInfo[0]].push(msg.uuid);
                    }
                }
            }
            break;
        case types.DELETE_CHANNEL_MESSAGES:
            for (let key in state.channelMessages){
                newChannelMessages[key] = [...state.channelMessages[key].filter(uuid => action.message_ids.indexOf(uuid) === -1)];
            }
            let newMessages = {}
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
