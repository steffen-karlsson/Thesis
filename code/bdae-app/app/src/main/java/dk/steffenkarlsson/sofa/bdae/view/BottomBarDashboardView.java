package dk.steffenkarlsson.sofa.bdae.view;

import android.content.Context;
import android.support.design.widget.FloatingActionButton;
import android.util.AttributeSet;
import android.view.View;

import butterknife.BindView;
import butterknife.OnClick;
import dk.steffenkarlsson.sofa.bdae.IActivityHandler;
import dk.steffenkarlsson.sofa.bdae.R;
import dk.steffenkarlsson.sofa.bdae.SubmitJobActivity;
import dk.steffenkarlsson.sofa.bdae.extra.TransitionAnimation;
import dk.steffenkarlsson.sofa.bdae.request.GetDatasetsRequest;
import dk.steffenkarlsson.sofa.networking.BaseRequest;
import dk.steffenkarlsson.sofa.networking.Result;

/**
 * Created by steffenkarlsson on 5/31/16.
 */
public class BottomBarDashboardView extends BasePagerControllerView {

    public enum RequestType {
        DATASETS
    }

    @BindView(R.id.fab)
    protected FloatingActionButton mAddNewJob;

    public BottomBarDashboardView(Context context) {
        super(context);
    }

    public BottomBarDashboardView(Context context, AttributeSet attrs) {
        super(context, attrs);
    }

    @Override
    public boolean hasOptionsMenu() {
        return false;
    }

    @Override
    public void setContent(IActivityHandler handler) {
        super.setContent(handler);

        new GetDatasetsRequest()
                .withContext(handler.getActivity())
                .setOnRequestListener(mListener)
                .run(RequestType.DATASETS);
    }

    @Override
    protected int getLayoutResource() {
        return R.layout.content_dashboard_view;
    }

    @Override
    public boolean shouldCache() {
        return true;
    }

    @Override
    public View getRoot() {
        return this;
    }

    @OnClick(R.id.fab)
    public void onFabClicked() {
        mActivityHandler.launchActivity(mActivityHandler.getActivityIntent(
                mActivityHandler.getContext(), SubmitJobActivity.class, false),
                TransitionAnimation.IN_FROM_BOTTOM);
    }

    private BaseRequest.OnRequestListener mListener = new BaseRequest.OnRequestListener() {

        @Override
        public void onError(int id, int statusCode) {
            //TODO: Handle error
        }

        @Override
        public void onError(int id, int statusCode, Object error) {
        }

        @Override
        public void onSuccess(int id, Result result) {
            switch (result.statusCode) {
                case 204:
                    mActivityHandler.setNoDataVisible(true);
                    break;
                default:
                    break;
            }
            mActivityHandler.setLoadingSpinnerVisible(false);
        }

        @Override
        public void onProcessing() {
        }
    };
}
