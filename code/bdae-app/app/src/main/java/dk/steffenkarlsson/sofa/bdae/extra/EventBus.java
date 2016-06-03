package dk.steffenkarlsson.sofa.bdae.extra;

import com.squareup.otto.Bus;

/**
 * Created by steffenkarlsson on 6/1/16.
 */
public class EventBus {
    private static Bus mEventBusInstance = new Bus();

    public static Bus getInstance() {
        return mEventBusInstance;
    }

    private EventBus() {
    }
}
