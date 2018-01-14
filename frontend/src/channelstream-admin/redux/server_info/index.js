import {combineReducers} from '../../../../node_modules/redux/dist/redux';
import channels from './channels'
import serverStats from './server_stats';

const combinedReducers = combineReducers({serverStats, channels});
export default combinedReducers;
