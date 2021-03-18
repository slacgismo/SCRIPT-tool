import axios from "axios";
import { serverUrl } from "./Server";

let countyRes = [];
countyRes = axios.get(`${serverUrl}/county`);
export { countyRes };
