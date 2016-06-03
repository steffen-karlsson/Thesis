package dk.steffenkarlsson.sofa.bdae.extra;

import dk.steffenkarlsson.sofa.bdae.IActivityHandler;
import dk.steffenkarlsson.sofa.networking.BaseRequest;
import dk.steffenkarlsson.sofa.networking.Result;

/**
 * Created by steffenkarlsson on 6/3/16.
 */
public abstract class CustomRequestListener implements BaseRequest.OnRequestListener {

    private final IActivityHandler mActivityHandler;

    public CustomRequestListener(IActivityHandler handler) {
        this.mActivityHandler = handler;
    }

    @Override
    public void onProcessing() {
    }

    @Override
    public void onError(int id, int statusCode, Object error) {
    }

    @Override
    public void onError(int id, int statusCode) {
    }

    @Override
    public void onSuccess(int id, Result result) {
        mActivityHandler.setLoadingSpinnerVisible(false);
        switch (result.statusCode) {
            case 204:
                mActivityHandler.setNoDataVisible(true);
                return;
            default:
                onData(id, result);
                return;
        }
    }

    protected abstract void onData(int id, Result result);
}
