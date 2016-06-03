package dk.steffenkarlsson.sofa.bdae.extra;

import android.content.Context;

import dk.steffenkarlsson.sofa.bdae.R;

/**
 * Created by steffenkarlsson on 6/3/16.
 */
public class DeviceUtils {

    public static boolean isOnTablet(Context context) {
        return context.getResources().getBoolean(R.bool.isTablet);
    }
}
