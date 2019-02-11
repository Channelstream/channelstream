'use strict';

export const types = {
    SET_CHANNEL_STATES: 'chatView/SET_CHANNEL_STATES',
    DEL_CHANNEL_STATE: 'chatView/DEL_CHANNEL_STATE',
    ADD_CHANNEL_USERS: 'chatView/ADD_CHANNEL_USERS',
    DEL_CHANNEL_USERS: 'chatView/DEL_CHANNEL_USERS'
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
    addChannelUsers: (channel, usersList) => ({
        type: types.ADD_CHANNEL_USERS,
        channel: channel,
        users: usersList
    }),
    removeChannelUsers: (channel, usersList) => ({
        type: types.DEL_CHANNEL_USERS,
        channel: channel,
        users: usersList,
    })

};


let addChannelUsers = (usersState, channelName, userList) => {
    if (!usersState.hasOwnProperty(channelName)) {
        usersState[channelName] = [];
    }
    for (let user of userList) {
        if (usersState[channelName].indexOf(user) === -1) {
            usersState[channelName].push(user);
        }
    }
};

let delChannelUsers = (usersState, channelName, userList) => {
    if (!usersState.hasOwnProperty(channelName)) {
        return;
    }
    for (let user of userList) {
        let foundIndex = usersState[channelName].indexOf(user);
        if (foundIndex !== -1) {
            usersState[channelName].splice(foundIndex, 1);
        }
    }
};

let cloneChannelUsers = (state) => {
    let channelsUsers = {};
    for (let key in state) {
        channelsUsers[key] = [...state[key]];
    }
    return channelsUsers;
};


const INITIAL_STATE = {states: {}, allIds: [], users: {}};

export const reducer = (state = INITIAL_STATE, action) => {
    if (typeof state === 'undefined') {
        return INITIAL_STATE;
    }
    switch (action.type) {
        case types.SET_CHANNEL_STATES:
            state = {
                states: {...state.states},
                allIds: [...state.allIds],
                users: cloneChannelUsers(state.users)
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
                addChannelUsers(state.users, channelState[0], channelState[1].users);
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
                users: cloneChannelUsers(state.users),
                allIds: newArray
            };
            break;
        case types.ADD_CHANNEL_USERS:
            state = {
                states: {...state.states},
                allIds: [...state.allIds],
                users: cloneChannelUsers(state.users)
            };
            addChannelUsers(state.users, action.channel, action.users);
            break;
        case types.DEL_CHANNEL_USERS:
            state = {
                states: {...state.states},
                allIds: [...state.allIds],
                users: cloneChannelUsers(state.users)
            };
            delChannelUsers(state.users, action.channel, action.users);
            break;
    }
    return state;
};

export default reducer
