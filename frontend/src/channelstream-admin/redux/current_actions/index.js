'use strict';

export const types = {
    CURRENT_ACTION_START: 'CURRENT_ACTION_START',
    CURRENT_ACTION_FINISH: 'CURRENT_ACTION_FINISH',
    CURRENT_ACTION_ERROR: 'CURRENT_ACTION_ERROR'
}

const update = (state, mutations) => Object.assign({}, state, mutations);

export const actions = {
    currentActionStart: (subtype, payload) => ({
        type: types.CURRENT_ACTION_START,
        subtype: subtype,
        payload: payload
    }),
    currentActionFinish: (subtype, payload) => ({
        type: types.CURRENT_ACTION_FINISH,
        subtype: subtype,
        payload: payload
    }),
    currentActionError: (subtype, error) => ({
        type: types.CURRENT_ACTION_ERROR,
        subtype: subtype,
        payload: error
    })
};

const INITIAL_STATE = {
    active: [],
    failed: {},
    activeCount: 0
};

export const reducer = (state = INITIAL_STATE, action) => {
    switch (action.type) {
        case types.CURRENT_ACTION_START:
            state = {
                ...state,
                active: [...state.active, action.subtype]
            };
            break;
        case types.CURRENT_ACTION_FINISH:
            state = {
                ...state,
                active: state.active.filter(item => action.subtype !== item)
            };
            break;
        case types.CURRENT_ACTION_ERROR:
            state = {
                ...state,
                active: state.active.filter(item => action.subtype !== item),
                failed: {...state.failed, [action.subtype]: action.payload}
            };
            break;
    }
    state.activeCount = state.active.length
    return state;
};

export default reducer;
