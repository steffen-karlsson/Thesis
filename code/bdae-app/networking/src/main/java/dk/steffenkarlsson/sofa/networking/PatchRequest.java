package dk.steffenkarlsson.sofa.networking;

import com.squareup.okhttp.Request;

/**
 * Created by steffenkarlsson on 23/12/14.
 */
@SuppressWarnings("ALL")
public abstract class PatchRequest<T> extends AbstractBodyRequest<T> {

    protected PatchRequest(String url) {
        super(url);
    }

    @Override
    protected Request finalizeRequest(Request.Builder builder) {
        builder.patch(getData());
        return builder.build();
    }
}
