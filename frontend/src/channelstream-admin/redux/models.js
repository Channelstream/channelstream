'use strict';

export const currentActions = {
    state: {
        active: [],
        failed: {},
        activeCount: 0
    }, // initial state
    reducers: {
        // handle state changes with pure functions
        start(state, payload) {
            return {
                ...state,
                active: [...state.active, payload.subtype]
            }
        },
        finish(state, payload) {
            return {
                ...state,
                active: state.active.filter(item => payload.subtype !== item)
            }
        },
        error(state, payload) {
            return {
                ...state,
                active: state.active.filter(item => payload.subtype !== item),
                failed: {...state.failed, [payload.subtype]: payload.payload.error}
            }
        },
    }
};

export const serverStats = {
    state: {
        uptime: undefined,
        remembered_user_count: 0,
        unique_user_count: 0,
        total_connections: 0,
        total_channels: 0,
        total_unique_messages: 0,
        total_messages: 0
    }, // initial state
    reducers: {
        // handle state changes with pure functions
        set(state, payload) {
            return {...payload}
        }
    }
};

export const channelStats = {
    state: [], // initial state
    reducers: {
        // handle state changes with pure functions
        set(state, payload) {
            return [...payload]
        }
    }
};
