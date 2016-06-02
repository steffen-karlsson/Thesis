package dk.steffenkarlsson.sofa.bdae.extra;

import android.content.Context;
import android.content.SharedPreferences;
import android.text.TextUtils;

import dk.steffenkarlsson.sofa.bdae.R;

/**
 * Created by steffenkarlsson on 5/31/16.
 */
public class ConfigurationHandler {

    private static final String KEY_INSTANCE_NAME = "KEY_INSTANCE_NAME";
    private static final String KEY_GATEWAY_IDENTIFIER = "KEY_GATEWAY_IDENTIFIER";
    private static final String KEY_API_HOSTNAME = "KEY_API_HOSTNAME";

    private static final String GATEWAY_PATTERN = "sofa:%s:gateway:%s";

    private Context mContext;
    private SharedPreferences mSharedPreferences;
    private boolean mHasData = false;

    private static ConfigurationHandler ourInstance = new ConfigurationHandler();

    public static ConfigurationHandler getInstance() {
        return ourInstance;
    }

    private ConfigurationHandler() {
    }

    public void initialize(Context context) {
        this.mContext = context;

        SharedPreferences sp = getSharedPreferences();
        this.mHasData = sp.contains(KEY_INSTANCE_NAME) && sp.contains(KEY_GATEWAY_IDENTIFIER) && sp.contains(KEY_API_HOSTNAME);
    }

    public void setup(String apiHostname, String instanceName, String gatewayIdentifier) {
        if (TextUtils.isEmpty(apiHostname) || TextUtils.isEmpty(instanceName) || TextUtils.isEmpty(gatewayIdentifier))
            throw new IllegalArgumentException("One of the three arguments is null or empty");

        this.mHasData = true;
        SharedPreferences sp = getSharedPreferences();
        SharedPreferences.Editor editor = sp.edit();
        editor.putString(KEY_API_HOSTNAME, apiHostname);
        editor.putString(KEY_INSTANCE_NAME, instanceName);
        editor.putString(KEY_GATEWAY_IDENTIFIER, gatewayIdentifier);
        editor.apply();
    }

    public boolean hasData() {
        return mHasData;
    }

    public String getApiHostName() {
        if (hasData())
            return getSharedPreferences().getString(KEY_API_HOSTNAME, "");
        return "";
    }

    public String getInstanceName() {
        if (hasData())
            return getSharedPreferences().getString(KEY_INSTANCE_NAME, "");
        return "";
    }

    public String getGateway() {
        if (hasData()) {
            String gatewayIdentifier = getSharedPreferences().getString(KEY_GATEWAY_IDENTIFIER, "");
            String instanceName = getInstanceName();
            return String.format(GATEWAY_PATTERN, instanceName, gatewayIdentifier);
        }
        return "";
    }

    public void clear() {
        getSharedPreferences().edit().clear().apply();
    }

    private SharedPreferences getSharedPreferences() {
        if (mSharedPreferences == null)
            mSharedPreferences = mContext.getSharedPreferences(mContext.getString(R.string.shared_preferences_name), Context.MODE_PRIVATE);
        return mSharedPreferences;
    }
}
