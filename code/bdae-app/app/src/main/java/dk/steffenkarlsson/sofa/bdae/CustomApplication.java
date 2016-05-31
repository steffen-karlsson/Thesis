package dk.steffenkarlsson.sofa.bdae;

import android.app.Application;

import dk.steffenkarlsson.sofa.bdae.extra.ConfigurationHandler;

/**
 * Created by steffenkarlsson on 5/31/16.
 */
public class CustomApplication extends Application {

    @Override
    public void onCreate() {
        super.onCreate();

        ConfigurationHandler.getInstance().initialize(getApplicationContext());
    }
}
